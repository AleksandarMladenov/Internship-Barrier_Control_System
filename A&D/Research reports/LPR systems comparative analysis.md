1. Introduction

Automatic license plate recognition (ALPR) is essential in intelligent transport systems, parking automation, and law enforcement. Recognition performance can be significantly reduced by adverse conditions including poor illumination, weather artifacts, high-speed vehicle motion, and plate orientation.
This research surveys leading frameworks, analyzes their robustness, and proposes integration strategies suited for server-side workflows.

2. Frameworks Considered
Tesseract OCR (Apache-2.0)

A lightweight OCR engine efficient on CPU and suitable for clean plate crops. It struggles under noise, blur, or low light.

EasyOCR (Apache-2.0)

A deep learning OCR library with good support for diverse fonts and languages. It is easier to integrate than training custom models but benefits from GPU acceleration.

OpenALPR (AGPL-3.0 / Rekor commercial)

Offers an end-to-end pipeline but the open-source version is outdated and less robust in complex conditions. It works well as a baseline.

YOLO-based Detection + OCR

The most modern approach, using YOLO for plate detection and OCR engines like EasyOCR or PaddleOCR for recognition. YOLO is robust under challenging conditions but requires GPU for real-time use.

3. Evaluation Criteria

| **Criterion**                | **Definition**                                                     |
| ---------------------------- | ------------------------------------------------------------------ |
| **Accuracy & Robustness**    | Performance under low light, weather, motion, and angle distortion |
| **Computational Efficiency** | Inference speed on CPU/GPU                                         |
| **Ease of Integration**      | Simplicity of embedding in a FastAPI or microservice backend       |
| **Licensing Constraints**    | Suitability for commercial deployment                              |


4. Condition-Specific Observations

Low-light / Nighttime:
YOLO-based systems paired with image enhancement (CLAHE or Retinex) sustain accuracy, while Tesseract performance declines sharply. EasyOCR benefits from preprocessing and maintains reasonable accuracy.

Adverse Weather (Rain, Snow, Fog):
YOLO-based models trained with augmentation outperform classical methods. Dehazing and denoising improve OCR results, though OpenALPR suffers heavily.

Motion Blur / High-Speed Vehicles:
YOLO still detects plates, but recognition accuracy declines unless deblurring or temporal aggregation is applied. EasyOCR combined with temporal voting across frames can recover accuracy.

Strong Angles / Perspective Distortion:
YOLO OBB (Oriented Bounding Box) models and OpenCV homography rectification improve detection and recognition significantly.

5. Comparative Table

| **Stack**                            | **Accuracy (Adverse)** | **Speed (CPU)** | **Speed (GPU)** | **Ease of Use** | **License** | **Overall Notes**                              |
| ------------------------------------ | ---------------------: | --------------: | --------------: | --------------: | ----------- | ---------------------------------------------- |
| **YOLO + OCR (EasyOCR / PaddleOCR)** |                   High |             Low |       Very High |          Medium | AGPL (YOLO) | Most balanced; robust in all conditions        |
| **YOLO OBB + OCR**                   |                   High |             Low |            High |          Medium | AGPL        | Excellent for angled or skewed plates          |
| **EasyOCR + OpenCV**                 |                 Medium |          Medium |            High |            High | Apache-2.0  | Strong prototyping option; needs preprocessing |
| **Tesseract + OpenCV**               |                    Low |   **Very High** |               – |            High | Apache-2.0  | Works only for clean, frontal, well-lit crops  |
| **OpenALPR (Open-source)**           |                    Low |            High |          Medium |            High | AGPL        | Outdated but still a good baseline             |

6. Integration into a Server-Side Workflow

A practical workflow integrates YOLO for detection, OpenCV for preprocessing, and EasyOCR for recognition.
The system is deployed as a FastAPI microservice, containerized with Docker, and optimized for:

GPU inference using TensorRT (NVIDIA)

CPU inference using ONNX Runtime

Additional backend components include:

PostgreSQL for structured storage.

Object storage (e.g., MinIO) for captured plate images.

Prometheus + Grafana for monitoring and observability.

7. Benchmarking Protocol

To evaluate systems fairly, the following datasets and metrics are recommended:

Datasets

CCPD (Weather, Blur, Tilt)

UFPR-ALPR (Day/Night)

RodoSol-ALPR (Mixed conditions)

LP-Blur (Motion blur)

Metrics

| **Metric**                | **Purpose**                       |
| ------------------------- | --------------------------------- |
| Detection mAP             | Precision of plate localization   |
| Character Accuracy        | Correct individual character rate |
| Sequence Accuracy         | Full plate string match rate      |
| End-to-End Frame Accuracy | Complete frame success rate       |
| FPS Throughput / Latency  | Real-time performance measure     |

8. Cloud and Server Recommendations

| **Stage**                  | **Hardware / Service**      | **Notes**                              |
| -------------------------- | --------------------------- | -------------------------------------- |
| **Prototype / Local Dev**  | RTX 4060 / 4070             | Ideal for experiments and model tuning |
| **Production (GPU Cloud)** | Google Cloud G2 (L4 GPUs)   | Best price-performance                 |
|                            | AWS EC2 G6 (L4) / G5 (A10G) | Large ecosystem support                |
|                            | Azure NVads A10 v5          | Budget option with fractional GPUs     |


9. Conclusion and Logical Comparison

After comparing multiple OCR/ALPR frameworks across accuracy, efficiency, and ease of integration,
YOLO-based detection combined with EasyOCR and OpenCV preprocessing emerges as the most balanced choice.

Unlike Tesseract, which is lightweight but brittle under adverse conditions, or OpenALPR, which is outdated, YOLO offers robust detection across night, weather, blur, and angle variations.
EasyOCR provides flexible, multilingual recognition that is more robust than Tesseract, especially under non-ideal conditions.

The trade-off is computational demand, but modern GPUs such as NVIDIA L4 or A10G mitigate this, and efficient deployment pipelines (TensorRT, ONNX Runtime, FastAPI, Docker) ensure real-time performance.

Final Recommendation

YOLO + OpenCV + EasyOCR
This combination best satisfies the requirements for robustness, accuracy, and integration across all tested scenarios.
It is future-proof, scalable, and well-suited for both local and cloud deployments.

