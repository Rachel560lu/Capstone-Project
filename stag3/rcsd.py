import torch
from diffusers import StableDiffusionInpaintPipeline
from transformers import AutoImageProcessor, AutoModelForSemanticSegmentation
from PIL import Image
import numpy as np
import cv2
import os

# ================= 参数 =================
INPUT_IMAGE = "input/room.jpeg"          # LaMa 修复后的图片
OUTPUT_DIR = "output"
MAX_ITER = 10                            # 最大迭代次数
STRUCTURE_CLASSES = [0,3,5,8,14,18]    # 保留的结构类（墙/地板/天花板/窗户/门/窗帘）
OTHER_EXPAND = 30
OTHER_EXPAND_DOWN = 50

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ================= Step 1: 加载 SegFormer 模型 =================
MODEL_NAME = "nvidia/segformer-b3-finetuned-ade-512-512"
processor = AutoImageProcessor.from_pretrained(MODEL_NAME)
model = AutoModelForSemanticSegmentation.from_pretrained(MODEL_NAME)
model.eval()

# ================= Step 2: 加载 Stable Diffusion Inpainting =================
pipe = StableDiffusionInpaintPipeline.from_pretrained(
    "runwayml/stable-diffusion-inpainting",
    torch_dtype=torch.float16,
)
pipe = pipe.to("cuda")

# ================= Step 3: 迭代修复 =================
image = Image.open(INPUT_IMAGE).convert("RGB")

for iteration in range(MAX_ITER):
    print(f"=== 第 {iteration+1} 次检测与修复 ===")
    
    # ---------------- 分割 ----------------
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    upsampled_logits = torch.nn.functional.interpolate(
        logits, size=image.size[::-1], mode="bilinear", align_corners=False
    )
    pred_seg = upsampled_logits.argmax(dim=1)[0].cpu().numpy()
    
    # ---------------- 检查非结构类 ----------------
    all_classes = np.unique(pred_seg)
    non_structure_classes = [c for c in all_classes if c not in STRUCTURE_CLASSES]
    if not non_structure_classes:
        print("没有检测到非结构类，修复完成。")
        break
    
    print(f"检测到非结构类: {non_structure_classes}, 生成 mask 并 inpainting 修复...")
    
    # ---------------- 生成 mask ----------------
    mask = np.isin(pred_seg, non_structure_classes).astype(np.uint8) * 255
    structure_mask = np.isin(pred_seg, STRUCTURE_CLASSES).astype(np.uint8) * 255
    mask_final = cv2.bitwise_and(mask, cv2.bitwise_not(structure_mask))
    
    # 扩展 mask
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (OTHER_EXPAND*2+1, OTHER_EXPAND*2+1))
    mask_final = cv2.dilate(mask_final, kernel, iterations=1)
    
    mask_path = os.path.join(OUTPUT_DIR, f"mask_iter_{iteration+1}.png")
    cv2.imwrite(mask_path, mask_final)
    
    # 转 PIL
    mask_pil = Image.fromarray(mask_final)
    
    # ---------------- Stable Diffusion Inpainting ----------------
    prompt = (
        "empty modern room, completely bare walls, clean floor, clean ceiling, "
        "no furniture, no bed, no sofa, no chairs, realistic interior, soft natural light"
    )
    negative_prompt = "clutter, messy, furniture, bed, chair, sofa, fan"
    
    with torch.autocast("cuda"):
        result = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=image,
            mask_image=mask_pil,
            num_inference_steps=50,
            guidance_scale=7.5,
        ).images[0]
    
    image = result  # 下一轮迭代使用修复结果
    result_path = os.path.join(OUTPUT_DIR, f"image_iter_{iteration+1}.png")
    image.save(result_path)
    print(f"迭代 {iteration+1} 修复结果已保存: {result_path}")

# ================= 保存最终结果 =================
final_image_path = os.path.join(OUTPUT_DIR, "final_empty_room.png")
image.save(final_image_path)
print(f"最终空房间图片已保存: {final_image_path}")
