# RyzenAI Object Detection: Step-by-Step Run Test Guide

This guide documents the exact steps, commands, and important notes for using RyzenAI SW to quantize the onnx model using NPU on modern ryzen AI hardware, including common pitfalls and explanations for each step.

---

## Step 1: List Conda Environments

To list all conda environments, run:

```pwsh
conda env list
```

If the environment you need (for example, `ryzen-ai-1.5.1`) does not appear in the list, see the environment creation instructions at:
https://ryzenai.docs.amd.com/en/latest/inst.html

## Step 2: Create a Working Copy of the Environment (Optional Path)


To create a working copy of the `ryzen-ai-1.5.1` environment, you can specify any path where you want the new environment to be created. Replace `<target_path>` with your desired location (e.g., `C:\Software\RyzenAI\envs\yolov8m_env`).

### 2.0 Clone the environment

You can clone the environment by name (default location) or by custom path:

**Option 1: Clone by name (default location):**
```pwsh
$env:RYZEN_AI_CONDA_ENV_NAME = "ryzen-ai-1.5.1"
conda create --name yolov8m_env --clone $env:RYZEN_AI_CONDA_ENV_NAME
```

**Option 2: Clone by custom path:**
```pwsh
$env:RYZEN_AI_CONDA_ENV_NAME = "ryzen-ai-1.5.1"
conda create --prefix C:\Software\RyzenAI\envs\yolov8m_env --clone $env:RYZEN_AI_CONDA_ENV_NAME
```

**Note:** When you create a conda environment using `--prefix` (a custom path), it will appear in `conda env list` only by its path, not by a name. This is normal and does not affect functionality. Activate it using its full path.

### 2.1 Copy the state file from the source environment to the clone

After cloning, copy the `state` file from the source environment's `conda-meta` directory to the destination clone's `conda-meta` directory. This helps preserve environment state information for some conda tools, in particular the environment variable for the source ryzen ai install path.

Example command (PowerShell):

```pwsh
Copy-Item "C:\Users\<your-username>\anaconda3\envs\ryzen-ai-1.5.1\conda-meta\state" "C:\Software\RyzenAI\envs\yolov8m_env\conda-meta\state" -Force
```

Adjust the source path as needed for your system.

### 2.2 Activate the cloned environment (if not already activated)

```pwsh
conda activate C:\Software\RyzenAI\envs\yolov8m_env
```

## Step 3: Test the NPU Environment with Quicktest

After creating the copy of the ryzen conda environment and activating it, verify the Ryzen AI Software installation using quicktest.

Run the test:

   ```pwsh
   cd "$($env:RYZEN_AI_INSTALLATION_PATH)/quicktest"
   python quicktest.py
   ```

The `quicktest.py` script sets up the environment and runs a simple CNN model.

**Example expected output:**

```
I20250825 15:51:04.224241  3996 vitisai_compile_model.cpp:1157] Vitis AI EP Load ONNX Model Success
[Vitis AI EP] No. of Operators :   NPU   398 VITIS_EP_CPU     2 
[Vitis AI EP] No. of Subgraphs :   NPU     1 Actually running on NPU     1
Test Passed
```

If you see `Test Passed` and NPU operators/subgraphs, the model is running on the NPU and the Ryzen AI Software installation was successful.

## Step 4: OPTIONAL: Manually Install Ultralytics from Wheel (No Dependency Checks)

In case the automatic requirements checks fiddle with installed requirements, you may need to manually install ultralytics from a previous version wheel.
If you must manually install a specific version of Ultralytics from a wheel file, without letting pip resolve or change any dependencies. This prevents pip from upgrading or downgrading critical packages (like numpy or onnxruntime) that are required for NPU support.

**Why this version?**
- Ultralytics 8.2.42 less likely to have dependency conflicts with the hardcoded requirements of RyzenAI 1.5.1. Newer versions may require incompatible dependencies and break NPU support.

**Why install from a wheel and use --no-deps?**
- Installing from a wheel file (e.g., `ultralytics-8.2.42-py3-none-any.whl`) ensures you get the exact version you want, even if it is no longer available on PyPI.
- The `--no-deps` flag tells pip not to install or change any dependencies, so your environment's critical packages remain untouched.

**Command:**

```pwsh
pip install C:\Software\RyzenAI\runtest\ultralytics-8.2.42-py3-none-any.whl --no-deps
```

**Do not** use `pip install ultralytics` or add it to requirements.txt, as this will trigger dependency resolution and may break your NPU environment.



## Step 5: Install Tutorial-Specific Dependencies (from the correct folder!)

**You must switch to the tutorial's object_detection folder before installing requirements.**

**Why this is crucial:**
- The RyzenAI installer and the tutorial each have their own `requirements.txt` files. The installer’s requirements are for the base NPU stack, but the tutorial’s `requirements.txt` (in `tutorial/object_detection/`) is specifically for the object detection demo and includes extra packages (like torch, pycocotools, etc.) needed for YOLOv8 and model export.
- If you run `pip install -r requirements.txt` from the wrong folder, you may install the wrong set of dependencies, which can break your environment or leave out required packages for the demo.

**Step-by-step:**
### 5.1. Change directory to the tutorial folder:
   ```pwsh
   cd C:\Software\RyzenAI\RyzenAI-SW\tutorial\object_detection
   ```
### 5.2. (If you must follow the tutorial exactly) You can run:
   ```pwsh
   pip install -r requirements.txt
   ```
   - This will deploy the object detection tutorial specific requirements.
      May overwrite NPU-optimized torch/torchvision. If this happens, review if the steps were followed.

### 5.3. OPTIONAL: (if stuff still breaks, should not be necessary) If you have all required wheels locally, use:
   ```pwsh
   pip install --no-index --find-links=. -r requirements.txt
   ```
   - Do this only if you know why this is necessary, this section will be deleted in the future.

**Summary:**
- Always run the requirements install from the correct tutorial folder to get the right dependencies for the demo.
- If you see NPU support lost after this step, rerun the AMD/optimized wheel installs for torch, torchvision, onnxruntime, etc.

**Do not** add Ultralytics to requirements.txt or install it with `pip install ultralytics`, as this will trigger dependency resolution and may break your NPU environment. Always install Ultralytics manually from the wheel as described in Step 4.


## Step 6. Export YOLOv8 Model to ONNX (with PyTorch 2.6+ workaround)

### Why?
ONNX format is required for quantization and NPU deployment.

### PyTorch 2.6+ Issue and Workaround
If you are using PyTorch 2.6 or newer, loading YOLOv8 .pt files may fail with a `weights_only` error due to a new default in torch.load. To force the old behavior and allow model export, set the following environment variable before running the export script:

```pwsh
$env:TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD="1"
```

This tells PyTorch to use `weights_only=False` by default, restoring compatibility with Ultralytics and YOLOv8 checkpoints.

### Steps
1. **Run the export script:**
   #### From the tutorial\object_detection folder in the ryzenai-sw repo path:
   Export the yolo model to onnx:
   ```powershell
   cd models
   $env:TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD="1"
   python export_to_onnx.py
   ```
   - This downloads `yolov8m.pt` and exports `yolov8m.onnx`.
   - If prompted to update Ultralytics, be cautious: updating may change ONNX Runtime versions and break NPU compatibility.

**Expected output:**
You should see a warning like:
```
UserWarning: Environment variable TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD detected, since the`weights_only` argument was not explicitly passed to `torch.load`, forcing weights_only=False.
```
and the export should complete successfully, producing `yolov8m.onnx`.


**Pitfall:**
- Make sure you are using the environment provided by the RyzenAI installer for NPU support.
- Do not update ONNX Runtime unless you know it is compatible with your NPU stack.

---

## Step 7: Run Inference on the Quantized Model (NPU)

### What & Why
After quantizing your ONNX model to XINT8, you should verify that it runs correctly on the NPU and produces valid results. This step ensures your quantized model is functional and that the NPU is being used for inference.

### Command Example (from tutorial/object_detection directory)
```pwsh
python run_inference.py --model_input models/yolov8m_XINT8.onnx --input_image test_image.jpg --output_image test_output_int8.jpg --device npu-int8
```
Make sure the paths to the model and images are correct relative to your current directory. The output image will be saved as `test_output_int8.jpg` in the same directory.

### Expected Output
- The script should run without errors and print inference progress and summary.
- You should see a new file: `test_output_int8.jpg`.
- If the NPU is used, you may see logs or a brief spike in NPU usage in Task Manager.

### What the Results Tell You
- If the output image is created and the script completes without errors, your quantized model is valid and NPU inference is working.
- The output image will show the model’s predictions (e.g., bounding boxes) on the test image.
- If you see errors or no output, check your model paths, NPU environment, and quantization steps.

---

## Root Issue and Resolution for Missing Bounding Boxes

### Root Cause
The YOLOv8 model quantized with XINT8 configuration experienced significant degradation in confidence values due to the use of `Concat` operations in the post-processing sub-graph. This led to missing bounding boxes and failed object detection during inference.
https://github.com/amd/RyzenAI-SW/tree/main/tutorial/object_detection#modification

### Steps to Reproduce the Issue
1. **Run Inference on the Quantized Model:**
   ```pwsh
   python run_inference.py --model_input models/yolov8m_XINT8.onnx --input_image test_image.jpg --output_image test_output_int8.jpg --device npu-int8
   ```
   - Observe the output image (`test_output_int8.jpg`) for missing bounding boxes.
   - Check the logs for low confidence values or absence of detections.

2. **Evaluate Model Accuracy:**
   ```pwsh
   python run_inference.py --model_input models/yolov8m_XINT8.onnx --evaluate --coco_dataset datasets/coco --device npu-int8
   ```
   - Confirm that the evaluation function fails to detect objects, indicating degraded accuracy.

### Steps to Fix the Issue
1. **Exclude Problematic Sub-Graphs:**
   Modify the quantization process to exclude the `Concat` operations causing degradation:
   ```pwsh
   python quantize_quark.py --input_model_path models/yolov8m.onnx \
                            --calib_data_path calib_images \
                            --output_model_path models/yolov8m_XINT8.onnx \
                            --config XINT8 \
                            --exclude_subgraphs "[/model.22/Concat_3], [/model.22/Concat_5]"
   ```

2. **Re-Quantize the Model:**
   - Ensure the updated quantized model (`models/yolov8m_XINT8.onnx`) is generated successfully.

### Outcome of Fix
- The quantized model now excludes the problematic sub-graphs, improving confidence values and detection accuracy.
- Bounding boxes and labels are visible in the output image (`test_output_int8.jpg`).

### Steps to Test and View Improvement
1. **Run Inference on the Updated Model:**
   ```pwsh
   python run_inference.py --model_input models/yolov8m_XINT8.onnx --input_image test_image.jpg --output_image test_output_int8.jpg --device npu-int8
   ```
   - Verify that bounding boxes and labels are present in the output image.

2. **Evaluate Model Accuracy:**
   ```pwsh
   python run_inference.py --model_input models/yolov8m_XINT8.onnx --evaluate --coco_dataset datasets/coco --device npu-int8
   ```
   - Confirm improved accuracy metrics (e.g., mAP, mAP50, mAP75).

3. **Visual Inspection:**
   - Open the output image (`test_output_int8.jpg`) and confirm that objects are correctly detected and labeled.

By following these steps, the issue of missing bounding boxes was resolved, and the quantized model's performance was significantly improved.

---

## Caveats: Excluding Sub-Graphs During Quantization

When using the quantization flag:

```
--exclude_subgraphs "[/model.22/Concat_3], [/model.22/Concat_5]"
```

### What are these exclusions?
- `/model.22/Concat_3` and `/model.22/Concat_5` are nodes (operations) in the YOLOv8 ONNX model, typically used to combine outputs (like bounding box coordinates and class confidences) before post-processing.
- Excluding them means these operations (and their connected sub-graphs) remain in floating-point precision (FP32) instead of being quantized to INT8.

### Real-world, general usage consequences:
1. **Accuracy Improvement:**  
   Excluding these nodes can prevent quantization errors that degrade detection accuracy, especially for post-processing steps sensitive to precision loss.

2. **Slightly Lower Performance:**  
   The excluded sub-graphs will run on the CPU (or in FP32 on the NPU if supported), not fully benefiting from INT8 acceleration. This may slightly reduce inference speed, but the impact is usually minor since these are small post-processing steps.

3. **Model Portability:**  
   The model is less “fully quantized,” which could affect deployment on hardware that requires all operations to be INT8. Most modern NPUs, however, support mixed-precision models.

4. **Maintainability:**  
   Exclusions are model- and version-specific. If the model architecture changes, the node names may change, requiring updates to the exclusion list.

**Summary:**  
Excluding these sub-graphs is a targeted workaround to preserve detection accuracy when quantization would otherwise break post-processing. The trade-off is a very minor loss in speed or hardware utilization, but a major gain in correct results. This is a common and accepted practice in real-world quantization workflows.

*This guide was generated to help future users avoid common issues and understand the reasoning behind each step.* -->
<!-- i have commented out this section because these are the legacy steps. once we manage to get the above to actually work at least once, we will enrich the steps above with the relevant / useful parts from the below.

## 1. Environment Setup

### Why?
A clean, compatible Python environment ensures all dependencies work together, especially for NPU support.

### Steps
1. **Open Anaconda Prompt or PowerShell.**
2. **Create or use a Conda environment:**
   ```powershell
   conda create -n ryzen-ai-1.5.1 python=3.10 -y
   conda activate ryzen-ai-1.5.1
   ```
   *Or use an existing environment if already set up.*
3. **Initialize Conda for PowerShell (first time only):**
   ```powershell
   conda init powershell
   # Restart your shell after this step
   ```
4. **Install dependencies:**
   ```powershell
   cd tutorial\object_detection
   pip install -r requirements.txt
   pip install ultralytics  # Not in requirements.txt, but required
   ```
   **Pitfall:** `ultralytics` is not in requirements.txt. Install it manually.

---

## 2. Export YOLOv8 Model to ONNX

### Why?
ONNX format is required for quantization and NPU deployment.

### Steps
1. **Run the export script:**
   ```powershell
   cd models
   python export_to_onnx.py
   ```
   - This downloads `yolov8m.pt` and exports `yolov8m.onnx`.
   - If prompted to update Ultralytics, be cautious: updating may change ONNX Runtime versions and break NPU compatibility.

**Pitfall:**
- Make sure you are using the environment provided by the RyzenAI installer for NPU support.
- Do not update ONNX Runtime unless you know it is compatible with your NPU stack.

---

## 3. Prepare COCO Dataset

### Why?
Calibration and evaluation require a dataset in the correct format.

### Steps
1. **Run the data preparation script:**
   ```powershell
   cd ..  # if in models
   python prepare_data.py
   ```
   - Downloads and extracts COCO val2017 images and annotations.
   - Converts COCO annotations to YOLO format.

**Pitfall:**
- Ensure you have enough disk space and a stable internet connection.

---

## 4. Quantize Model (XINT8 for NPU)

### Why?
INT8 quantization is typically best for NPU performance.

### Steps
1. **Run quantization:**
   ```powershell
   python quantize_quark.py --input_model_path models/yolov8m.onnx --calib_data_path datasets/coco/images/val2017 --output_model_path models/yolov8m_XINT8.onnx --config XINT8
   ```
   - This creates `yolov8m_XINT8.onnx`.
   - Warnings about missing custom ops for CPU can be ignored for NPU use.

**Pitfall:**
- You must specify both `--input_model_path` and `--calib_data_path`.
- If you see errors about missing compilers, they are only relevant for CPU custom ops, not NPU.

---

## 5. Run Inference on NPU

### Why?
To verify the quantized model runs on the NPU and produces results.

### Steps
1. **Run inference:**
   ```powershell
   python run_inference.py --model_input models\yolov8m_XINT8.onnx --input_image test_image.jpg --output_image test_output_int8.jpg --device npu-int8
   ```
   - This should use the NPU for inference.
   - Output is saved as `test_output_int8.jpg`.

**Pitfall:**
- If you see a warning like `Specified provider 'VitisAIExecutionProvider' is not in available provider names`, your environment is not set up for NPU. Only CPU and Azure providers are available.
- Make sure you have the correct ONNX Runtime (e.g., `onnxruntime-vitisai`) and that your environment matches the RyzenAI installer setup.

---

## General Tips
- Always use the provided environment or installer for NPU support.
- Avoid updating ONNX Runtime or Ultralytics unless you are sure of compatibility.
- If you encounter errors, check the README and this guide for common pitfalls.

---


