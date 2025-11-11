Capstone Project: Virtual Interior Redesign

Overview
This project delivers an end-to-end pipeline for virtual interior redesign from a furnished room photo to a realistically rendered, re-staged room. The system consists of three main stages: (1) furniture removal via segmentation and inpainting, (2) furniture selection and layout planning, and (3) structure-aware, style-controlled final rendering.

Architecture
1) Furniture Removal (Segmentation + Inpainting)
- Input: An indoor image with existing furniture.
- Segmentation: We use SegFormer, a transformer-based semantic segmentation model fine-tuned on ADE20K indoor scenes, to identify furniture objects.
- Masking: Furniture regions are converted into precise binary masks.
- Inpainting: Stable Diffusion Inpainting removes furniture and reconstructs the background to produce an empty-room image that preserves room structure and lighting as much as possible.

2) Furniture Selection and Layout Planning
- Assets: The 3D-Future dataset provides realistic furniture models and metadata.
- Inputs: User total budget, room type, style preference, and the generated empty-room image.
- Selection: An optimization module filters and selects suitable furniture items subject to budget and semantic fit.
- Layout Planning: A Vision-Language Model (VLM) proposes a furniture layout aligned with the room’s geometry and user preferences.
- Draft Visualization: Using OpenCV, the system generates a draft image with initial furniture placements over the empty-room background.

3) Room Rendering (Structure- and Style-Guided)
- Entry point: `stage3_room rendering/furnishing.py` orchestrates ControlNet-guided Stable Diffusion inpainting.
- Preprocessing: Unify resolution and color balance across the empty-room and drafted furniture images.
- Structure Extraction: Apply Canny edge detection to create an edge map that captures room geometry.
- Structure Conditioning: ControlNet consumes the edge map to guide Stable Diffusion, ensuring strict adherence to the original room layout while following text prompts for target style.
- Output: A photorealistic rendering of the redesigned room with the desired aesthetic and preserved layout, plus optional edge maps and harmonized variants.

Repository Structure
- stage1_clutter removal/ — Clutter removal MVP (segmentation + inpainting scripts)
- stage2_furniture selection/VirtualFurnishing/ — Furniture selection, layout planning, and draft visualization
  - data/ — Example inputs and metadata (e.g., model info JSONs, sample room image)
  - furniture_select/ — Selection notebooks and intermediate artifacts
  - inputs/ — User/config inputs (e.g., room.jpg, furniture.json)
  - layout_from_demo.py, layout_test.py — Layout and visualization entry points
- stage3_room rendering/ — Rendering pipeline with ControlNet + Stable Diffusion (`furnishing.py`, sample data)
- front_end/ — (Optional) UI or integration layer [if applicable]

Getting Started
Prerequisites
- OS: macOS, Linux, or Windows with compatible GPU recommended
- Python: 3.9–3.11
- GPU: NVIDIA GPU with CUDA for optimal performance (recommended)
- Models: Access to SegFormer (ADE20K-finetuned), Stable Diffusion Inpainting, and ControlNet (Canny)

Installation
1) Clone the repository
   git clone <your-repo-url>
   cd Capstone-Project

2) Create and activate a virtual environment
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

3) Install dependencies for Stage 2 (as a baseline)
   pip install -r "stage2_furniture selection/VirtualFurnishing/requirements.txt"

Usage
Stage 1 — Furniture Removal
Stage 2 — Furniture Selection and Layout Planning
Stage 3 — Realistic Rendering with Structure Guidance
Data and Models
- Segmentation: SegFormer (ADE20K indoor fine-tuned)
- Inpainting/Rendering: Stable Diffusion (Inpainting) + ControlNet (Canny)
- Furniture Assets: 3D-Future dataset (models and metadata)

Limitations
- Inpainting quality depends on mask accuracy and background complexity.
- Layout suggestions may require manual refinement for atypical geometries.
- Rendering fidelity varies with available checkpoints and hardware.

Acknowledgements
- ADE20K dataset and SegFormer authors
- Stable Diffusion and ControlNet communities
- 3D-Future dataset providers

License
Please see the repository license or add one if missing. Ensure compliance with the licenses of third-party models and datasets used.
