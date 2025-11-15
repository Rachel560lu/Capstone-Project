import diffusers  # 0.12.1
import math
import fire
import lovely_numpy
import lovely_tensors
import numpy as np
import os # <-- 新增：用于文件操作
import sys
import time
import torch
from contextlib import nullcontext
from diffusers.pipelines.stable_diffusion import StableDiffusionSafetyChecker
from einops import rearrange
from functools import partial
from ldm.models.diffusion.ddim import DDIMSampler
from ldm.util import create_carvekit_interface, load_and_preprocess, instantiate_from_config
from lovely_numpy import lo
from omegaconf import OmegaConf
from PIL import Image
from rich import print
from transformers import AutoFeatureExtractor
from torch import autocast
from torchvision import transforms

# --- 配置参数 ---
_GPU_INDEX = 0
_DEFAULT_CKPT = '105000.ckpt'
_DEFAULT_CONFIG = 'configs/sd-objaverse-finetune-c_concat-256.yaml'

def load_model_from_config(config, ckpt, device, verbose=False):
    """从配置文件和检查点加载模型"""
    print(f'Loading model from {ckpt}')
    pl_sd = torch.load(ckpt, map_location='cpu')
    sd = pl_sd['state_dict']
    model = instantiate_from_config(config.model)
    m, u = model.load_state_dict(sd, strict=False)
    if len(m) > 0 and verbose:
        print('missing keys:', m)
    if len(u) > 0 and verbose:
        print('unexpected keys:', u)

    model.to(device)
    model.eval()
    return model

@torch.no_grad()
def sample_model(input_im, model, sampler, precision, h, w, ddim_steps, n_samples, scale,
                 ddim_eta, x, y, z):
    """核心采样函数：生成指定视角图像"""
    precision_scope = autocast if precision == 'autocast' else nullcontext
    with precision_scope('cuda'):
        with model.ema_scope():
            c = model.get_learned_conditioning(input_im).tile(n_samples, 1, 1)
            # x: polar (极角), y: azimuth (方位角), z: radius (缩放)
            T = torch.tensor([math.radians(x), math.sin(
                math.radians(y)), math.cos(math.radians(y)), z])
            T = T[None, None, :].repeat(n_samples, 1, 1).to(c.device)
            c = torch.cat([c, T], dim=-1)
            c = model.cc_projection(c)
            cond = {}
            cond['c_crossattn'] = [c]
            # 编码输入图像作为条件
            cond['c_concat'] = [model.encode_first_stage((input_im.to(c.device))).mode().detach()
                                .repeat(n_samples, 1, 1, 1)]
            
            # 无条件引导
            if scale != 1.0:
                uc = {}
                uc['c_concat'] = [torch.zeros(n_samples, 4, h // 8, w // 8).to(c.device)]
                uc['c_crossattn'] = [torch.zeros_like(c).to(c.device)]
            else:
                uc = None

            shape = [4, h // 8, w // 8]
            samples_ddim, _ = sampler.sample(S=ddim_steps,
                                             conditioning=cond,
                                             batch_size=n_samples,
                                             shape=shape,
                                             verbose=False,
                                             unconditional_guidance_scale=scale,
                                             unconditional_conditioning=uc,
                                             eta=ddim_eta,
                                             x_T=None)
            
            x_samples_ddim = model.decode_first_stage(samples_ddim)
            return torch.clamp((x_samples_ddim + 1.0) / 2.0, min=0.0, max=1.0).cpu()

def preprocess_image(models, input_im, preprocess):
    '''
    :param input_im (PIL Image).
    :return input_im (H, W, 3) array in [0, 1].
    '''

    print('old input_im:', input_im.size)
    start_time = time.time()
    
    # 修复 NameError：使用 input_im 而非 raw_im 进行缩放检查
    # 确保图片尺寸不会过大（与原代码行为一致）
    if input_im.size[0] > 1536 or input_im.size[1] > 1536:
        print(f'Resizing input image from {input_im.size}...')
        # 注意: PIL 的 thumbnail 是原地操作 (in-place)
        input_im.thumbnail([1536, 1536], Image.Resampling.LANCZOS)
    
    # --- 实际预处理逻辑 ---
    if preprocess:
        # 使用 Carvekit 抠图
        input_im = load_and_preprocess(models['carvekit'], input_im)
        input_im = (input_im / 255.0).astype(np.float32)
        # (H, W, 3) array in [0, 1].
    else:
        # 简单缩放并混合白色背景
        input_im = input_im.resize([256, 256], Image.Resampling.LANCZOS)
        input_im = np.asarray(input_im, dtype=np.float32) / 255.0
        # (H, W, 4) array in [0, 1].

        # 应用正确的合成方法
        alpha = input_im[:, :, 3:4]
        white_im = np.ones_like(input_im)
        input_im = alpha * input_im + (1.0 - alpha) * white_im

        input_im = input_im[:, :, 0:3]
        # (H, W, 3) array in [0, 1].

    print(f'Infer foreground mask (preprocess_image) took {time.time() - start_time:.3f}s.')
    print('new input_im shape:', input_im.shape) # 打印形状以确认
    return input_im

def generate_views(
        input_path: str,
        output_dir: str,
        device_idx: int = _GPU_INDEX,
        ckpt: str = _DEFAULT_CKPT,
        config: str = _DEFAULT_CONFIG,
        preprocess: bool = True,
        scale: float = 3.0,
        ddim_steps: int = 75,
        h: int = 256,
        w: int = 256):
    """
    主运行函数：生成并保存指定视角的图片
    :param input_path: 输入图片文件路径
    :param output_dir: 输出图片保存目录
    :param device_idx: GPU 索引
    :param ckpt: 模型检查点文件
    :param config: 模型配置文件
    :param preprocess: 是否进行图片预处理（抠图）
    :param scale: Diffusion guidance scale
    :param ddim_steps: Diffusion inference steps
    """
    
    device = f'cuda:{device_idx}'
    config_obj = OmegaConf.load(config)

    # --- 1. 初始化模型 ---
    print('Instantiating models...')
    models = dict()
    models['turncam'] = load_model_from_config(config_obj, ckpt, device=device)
    models['carvekit'] = create_carvekit_interface()
    models['nsfw'] = StableDiffusionSafetyChecker.from_pretrained(
        'CompVis/stable-diffusion-safety-checker').to(device)
    models['clip_fe'] = AutoFeatureExtractor.from_pretrained(
        'CompVis/stable-diffusion-safety-checker')
    models['nsfw'].concept_embeds_weights *= 1.07
    models['nsfw'].special_care_embeds_weights *= 1.07

    # --- 2. 准备输入图片和输出目录 ---
    try:
        raw_im = Image.open(input_path).convert('RGBA')
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_path}")
        return
    except Exception as e:
        print(f"Error loading image: {e}")
        return

    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory created/verified: {output_dir}")

    # --- 3. 安全检查 ---
    safety_checker_input = models['clip_fe'](raw_im, return_tensors='pt').to(device)
    (_, has_nsfw_concept) = models['nsfw'](
        images=np.ones((1, 3)), clip_input=safety_checker_input.pixel_values)
        
    if np.any(has_nsfw_concept):
        print('!!! NSFW content detected. Aborting generation. !!!')
        return
    print('Safety check passed.')

    # --- 4. 预处理图片 ---
    input_im_np = preprocess_image(models, raw_im, preprocess)
    
    # 转换为模型输入格式
    input_im_tensor = transforms.ToTensor()(input_im_np).unsqueeze(0).to(device)
    input_im_tensor = input_im_tensor * 2 - 1
    input_im_tensor = transforms.functional.resize(input_im_tensor, [h, w])
    
    sampler = DDIMSampler(models['turncam'])
    ddim_eta = 1.0 # 默认值
    precision = 'fp32' # 默认值

    # --- 5. 定义并生成目标视角 ---
    # 方位角 (azimuth) 列表
    # 0度是正面，正值顺时针旋转
    azimuth_angles = [45, 90, 135, 180, 225, 270, 315] 
    
    # 极角 (polar/x) 和缩放 (radius/z) 保持不变
    polar_angle = 0.0 # x (垂直旋转)
    radius_zoom = 0.0 # z (缩放)
    
    n_samples = 1 # 每个角度只生成一张图片

    print(f"\nStarting generation for {len(azimuth_angles)} views...")

    for i, azimuth_y in enumerate(azimuth_angles):
        print(f"[{i+1}/{len(azimuth_angles)}] Generating view: Azimuth={azimuth_y}°")
        
        # 调用核心生成函数
        x_samples_ddim = sample_model(input_im_tensor, models['turncam'], sampler, precision, h, w,
                                      ddim_steps, n_samples, scale, ddim_eta, 
                                      polar_angle, azimuth_y, radius_zoom)

        # 转换为 PIL Image 并保存
        x_sample = x_samples_ddim[0]
        x_sample = 255.0 * rearrange(x_sample.cpu().numpy(), 'c h w -> h w c')
        output_im = Image.fromarray(x_sample.astype(np.uint8))
        
        # 保存文件
        # 文件名格式：<原文件名>_azimuth_<角度>.png
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_filename = os.path.join(
            output_dir, f"{base_name}_azimuth_{azimuth_y:03d}.png")
        output_im.save(output_filename)
        print(f"   -> Saved to: {output_filename}")

    print("\n✅ All views generated successfully!")


if __name__ == '__main__':
    # 使用 fire 允许通过命令行传递参数
    # 运行示例: python your_script_name.py --input_path 'path/to/your/image.png' --output_dir 'output_views'
    fire.Fire(generate_views)