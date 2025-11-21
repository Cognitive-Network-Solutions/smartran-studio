# NOTICE

SmartRAN Studio
Copyright 2025 Cognitive Network Solutions Inc.

This product includes software developed by third parties and is provided under their respective licenses.

---

## Branding

The CNS logos (`cnsLogo_lightmode.png`, `cnsLogo_darkmode.png`) are © Cognitive Network Solutions Inc. 2025. All rights reserved. These logos are not licensed under the Apache 2.0 license.

---

## Third-Party Software

### NVIDIA Sionna

**Copyright:** Copyright (c) 2021-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.  
**License:** Apache License 2.0  
**Source:** https://github.com/NVlabs/sionna  
**Description:** Link-level simulator for 6G physical layer research based on TensorFlow  

Sionna is licensed under the Apache License, Version 2.0. You may obtain a copy of the License at:
http://www.apache.org/licenses/LICENSE-2.0

**Citation:**
```
@article{sionna,
    title = {{Sionna: An Open-Source Library for Next-Generation Physical Layer Research}},
    author = {Hoydis, Jakob and Cammerer, Sebastian and {Ait Aoudia}, Fayçal and Vem, Avinash and Binder, Nikolaus and Marcus, Guillermo and Keller, Alexander},
    year = {2022},
    month = {03},
    journal = {arXiv preprint},
    online = {https://arxiv.org/abs/2203.11854}
}
```

---

### TensorFlow

**Copyright:** Copyright 2015-2024 The TensorFlow Authors. All Rights Reserved.  
**License:** Apache License 2.0  
**Source:** https://github.com/tensorflow/tensorflow  
**Description:** An Open Source Machine Learning Framework for Everyone  

TensorFlow is licensed under the Apache License, Version 2.0. You may obtain a copy of the License at:
http://www.apache.org/licenses/LICENSE-2.0

---

### NVIDIA RAPIDS

**Copyright:** Copyright (c) 2018-2024, NVIDIA CORPORATION.  
**License:** Apache License 2.0  
**Source:** https://github.com/rapidsai  
**Description:** Suite of software libraries and APIs for GPU-accelerated data science  

RAPIDS is licensed under the Apache License, Version 2.0. You may obtain a copy of the License at:
http://www.apache.org/licenses/LICENSE-2.0

**Components Used:**
- cuDF: GPU DataFrame library
- cuPy: NumPy-compatible array library for GPU
- RAPIDS container runtime environment

---

### ArangoDB

**Copyright:** Copyright 2014-2024 ArangoDB GmbH, Cologne, Germany  
**License:** Apache License 2.0  
**Source:** https://github.com/arangodb/arangodb  
**Description:** Native multi-model database with flexible data models for documents, graphs, and key-values  

ArangoDB is licensed under the Apache License, Version 2.0. You may obtain a copy of the License at:
http://www.apache.org/licenses/LICENSE-2.0

---

### NVIDIA Container Toolkit

**Copyright:** Copyright (c) 2017-2024, NVIDIA CORPORATION & AFFILIATES.  
**License:** Apache License 2.0  
**Source:** https://github.com/NVIDIA/nvidia-container-toolkit  
**Description:** Build and run containers leveraging NVIDIA GPUs  

---

### NVIDIA CUDA

**Copyright:** Copyright (c) 1993-2024 NVIDIA Corporation  
**License:** NVIDIA CUDA Toolkit End User License Agreement  
**Source:** https://developer.nvidia.com/cuda-zone  
**Description:** Parallel computing platform and programming model for NVIDIA GPUs  

**Note:** CUDA runtime libraries are redistributed as part of the RAPIDS container. Users must comply with the NVIDIA CUDA Toolkit EULA.

---

## Python Dependencies

This project also uses the following open-source Python libraries:

- **FastAPI** - MIT License - https://github.com/tianocore/edk2  
- **Uvicorn** - BSD 3-Clause License - https://github.com/encode/uvicorn
- **Pydantic** - MIT License - https://github.com/pydantic/pydantic
- **NumPy** - BSD 3-Clause License - https://github.com/numpy/numpy
- **python-arango** - MIT License - https://github.com/arangodb/python-arango

## JavaScript/Frontend Dependencies

- **React** - MIT License - https://github.com/facebook/react
- **Vite** - MIT License - https://github.com/vitejs/vite
- **Axios** - MIT License - https://github.com/axios/axios

---

## Standards and Specifications

This project implements specifications from the 3rd Generation Partnership Project (3GPP):

- **3GPP TR 38.901** - Study on channel model for frequencies from 0.5 to 100 GHz  
**Source:** https://www.3gpp.org/

---

## License Compliance

All third-party software components listed above retain their original licenses. SmartRAN Studio code (integration, CLI, web interface, and orchestration) is licensed under Apache License 2.0. See the LICENSE file in the root directory for details.

When redistributing this software, you must:
1. Include a copy of this NOTICE file
2. Include a copy of the Apache 2.0 LICENSE file
3. Preserve all copyright notices from third-party components
4. Comply with the terms of all third-party licenses

---

## Contact

For questions about licensing or attribution, please open an issue on the project repository.

---

Last Updated: November 2025

