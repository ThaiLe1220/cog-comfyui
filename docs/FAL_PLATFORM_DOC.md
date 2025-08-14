# Fal.ai Platform Documentation

## Core Concepts

Understanding these essential terms will help you follow the tutorials and deploy your first model successfully.

### App

An **App** is a Python class that wraps your AI model for deployment. Your app defines what packages it needs, how to load your model, and how users interact with it.

```python
class MyApp(fal.App):
    machine_type = "GPU-H100"  # Choose your hardware

    def setup(self):
        # Load your model here
        # Executed on each runner

    @fal.endpoint("/")
    def generate(self, input_data):
        # Your endpoint logic here—usually a model call
```

### Machine Type

**Machine Type** specifies the hardware (CPU or GPU) your app runs on. Choose based on your model's needs: "CPU" for lightweight models, "GPU-H100" for most AI models, or "GPU-B200" for large models.

### Runner

A **Runner** is a compute instance that executes your app using your chosen machine type. Runners automatically start when requests arrive and shut down when idle to save costs.

### Endpoint

An **Endpoint** is a function in your app that users can call via API. It defines how your model processes inputs and returns outputs.

### Playground

Each endpoint gets an automatic **Playground** - a web interface where you can test your model with different inputs before integrating it into your application.

### fal run vs fal deploy

- **`fal run`**: Test your app on a single cloud gpu during development. Creates a temporary URL that disappears when you stop the command.

- **`fal deploy`**: Deploy your app to production. Creates a permanent URL that stays available until you delete it.

Use `fal run` while building and testing, then `fal deploy` when ready for production use.

---

## Deploy Models with Custom Containers

fal now supports running apps within custom Docker containers, providing greater flexibility and control over your environment.

### Example: Using Custom Containers with fal Apps

Here's a complete example demonstrating how to use custom containers with fal.

```python
import fal

from fal.container import ContainerImage

dockerfile_str = """
FROM python:3.11

RUN apt-get update && apt-get install -y ffmpeg
RUN pip install pyjokes ffmpeg-python
"""

custom_image = ContainerImage.from_dockerfile_str(
    dockerfile_str,
    registries={
        "https://my.registry.io/": {
            "username": <username>,
            "password": <password>,
        },
    },
)

class Test(fal.App, kind="container", image=custom_image):
    machine_type = "GPU"

    requirements = ["torch"]

    def setup(self):
        import subprocess
        subprocess.run(["nvidia-smi"])

    @fal.endpoint("/")
    def index(self):
        return "Hello, World!"
```

### Detailed Explanation

**Importing fal and ContainerImage:**
```python
import fal
from fal.container import ContainerImage
```

**Creating a Dockerfile String:** A multi-line string (`dockerfile_str`) is defined, specifying the base image as `python:3.11`, and installing ffmpeg and pyjokes packages.

```dockerfile
dockerfile_str = """
FROM python:3.11

RUN apt-get update && apt-get install -y ffmpeg
RUN pip install pyjokes ffmpeg-python
"""
```

> **Version mismatch**
> 
> Ensure that the Python version in the Dockerfile matches the Python version in your local environment that you use to run the app.
> 
> This is required to avoid any compatibility issues. We use pickle to serialize the app under the hood, and the Python versions must match to avoid any serialization issues.
> 
> That being said, we are constantly working on improving this experience.

Alternatively, you can use a Dockerfile path to specify the Dockerfile location:

```python
import pathlib
PWD = Path(__file__).resolve().parent

class Test(fal.App, kind="container", image=ContainerImage.from_dockerfile(f"{PWD}/Dockerfile")):
```

### Running the App

To run the app, save the code to a file (e.g., `test_container.py`) and execute it using the `fal run` command:

```bash
fal run test_container.py
```

This example demonstrates how to leverage Docker containers in fal, enabling customized execution environments for your apps. For more details and advanced usage, refer to the fal Container Documentation.

---

## Use a Custom Container Image

The easiest way to understand how to run a containerized application is to see an example. Let's convert the example from the previous section into a containerized application.

> **Container-based example app**
> 
> Check out the container-based example app for understanding the basics of running a containerized application on fal.

```python
import fal
from fal.container import ContainerImage
from fal.toolkit import Image, optimize

from pydantic import BaseModel, Field

dockerfile_str = """
FROM python:3.11

RUN apt-get update && apt-get install -y ffmpeg

RUN python -m venv .venv
ENV PATH="$PWD/.venv/bin:$PATH"
RUN pip install "accelerate" "transformers>=4.30.2" "diffusers>=0.26" "torch>=2.2.0"
"""


class Input(BaseModel):
    prompt: str = Field(
        description="The prompt to generate an image from.",
        examples=[
            "A cinematic shot of a baby racoon wearing an intricate italian priest robe.",
        ],
    )


class Output(BaseModel):
    image: Image = Field(
        description="The generated image.",
    )


class FalModel(
    fal.App,
    image=ContainerImage.from_dockerfile_str(dockerfile_str),
    kind="container",
  ):
    machine_type = "GPU"

    def setup(self) -> None:
        import torch
        from diffusers import AutoPipelineForText2Image

        # Load SDXL
        self.pipeline = AutoPipelineForText2Image.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0",
            torch_dtype=torch.float16,
            variant="fp16",
        )
        self.pipeline.to("cuda")

        # Apply fal's spatial optimizer to the pipeline.
        self.pipeline.unet = optimize(self.pipeline.unet)
        self.pipeline.vae = optimize(self.pipeline.vae)

        # Warm up the model.
        self.pipeline(
            prompt="a cat",
            num_inference_steps=30,
        )

    @fal.endpoint("/")
    def text_to_image(self, input: Input) -> Output:
        result = self.pipeline(
            prompt=input.prompt,
            num_inference_steps=30,
        )
        [image] = result.images
        return Output(image=Image.from_pil(image))
```

Voila! 🎉 The highlighted changes are the only modifications you need to make; the rest remains your familiar fal application.

> **Dockerfile Keywords**
> 
> Please check our Dockerfile best practices for more information on how to optimize your Dockerfile.

### fal Specific Considerations

When deploying your application on fal, you don't need to worry about enabling Docker Buildx or BuildKit. We take care of it for you. However, you can follow the guidelines mentioned above to create efficient Dockerfiles that will help speed up the build process and reduce resource consumption.

#### 1. File Upload Instead of COPY

`COPY` and `ADD` (from local filesystem) are not supported as of now to copy files into the container from the host. Instead you can use fal's `fal.toolkit` to upload files and refer them in the container using links.

> **Note**
> 
> If you are curious about the differences between COPY and ADD, check out the following link.

```python
json_url = File.from_path("my-file.json", repository="cdn").url

dockerfile_str = f"""
FROM python:3.11-slim
RUN apt-get update && apt-get install -y curl
RUN curl '{json_url}' > my-file.json
"""
```

or you can use `ADD` to directly download the file from the URL:

```python
json_url = File.from_path("requirements.txt", repository="cdn").url

dockerfile_str = f"""
FROM python:3.11-slim
ADD {json_url} /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
"""
```

### Using Private Docker Registries

To use private docker registries, you need to provide registry credentials like so:

#### Dockerhub

```python
class FalModel(
    fal.App,
    kind="container",
    image=ContainerImage.from_dockerfile_str(
        "FROM myuser/image:tag",
        registries={
            "https://index.docker.io/v1/": {
                "username": "myuser",
                "password": "$DOCKERHUB_TOKEN",  # use `fal secrets set` first to create this secret
            },
        },
    ),
)
    ...
```

#### Google Artifact Registry

```python
class FalModel(
    fal.App,
    kind="container",
    image=ContainerImage.from_dockerfile_str(
        "FROM europe-west1-docker.pkg.dev/myuser/image:tag",
        registries={
            "https://europe-west1-docker.pkg.dev": {
                "username": "oauth2accesstoken",
                "password": "$GCP_TOKEN",  # use `fal secrets set` first to create this secret
            },
        },
    ),
)
    ...
```

#### Amazon Elastic Container Registry

```python
class FalModel(
    fal.App,
    kind="container",
    image=ContainerImage.from_dockerfile_str(
        "FROM 123456789012.dkr.ecr.us-east-1.amazonaws.com/image:tag",
        registries={
            "https://1234567890.dkr.ecr.us-east-1.amazonaws.com": {
                "username": "AWS",
                # Use `aws ecr get-login-password --region us-east-1` to get a token. Note that they only last
                # 12 hours so it is better to just create them dynamically here instead of creating one and
                # setting it as a `fal secret`.
                # https://awscli.amazonaws.com/v2/documentation/api/latest/reference/ecr/get-login-password.html
                "password": aws_token,
            },
        },
    ),
)
    ...
```

### Build Secrets

We currently only support secret mounts.

```python
class FalModel(
    fal.App,
    kind="container",
    image=ContainerImage.from_dockerfile_str(
        """
        FROM python:3.11
        RUN --mount=type=secret,id=aws-key-id,env=AWS_ACCESS_KEY_ID \
            --mount=type=secret,id=aws-secret-key,env=AWS_SECRET_ACCESS_KEY \
            --mount=type=secret,id=aws-session-token,env=AWS_SESSION_TOKEN \
            aws s3 cp ...
        """,
        secrets={
            # use `fal secrets set` first to create these secrets
            "aws-key-id": "$AWS_ACCESS_KEY_ID",
            "aws-secret-key": "$AWS_SECRET_ACCESS_KEY",
            "aws-session-token": "$AWS_SESSION_TOKEN",
        },
    ),
):
    ...
```

---

## Deploy to Production

Deploy your models to production environments with confidence using the right deployment strategies and configurations. This guide focuses on model deployment patterns, authentication modes, and configuration best practices.

### Deployment Types

#### Ephemeral Deployments

For development and testing, use ephemeral deployments with `fal run`.

```bash
fal run MyApp::path/to/myapp.py
```

Once you kill the `fal run` process in your terminal, the ephemeral deployment will be destroyed.

#### Persistent Deployments

To permanently deploy your application or update/redeploy existing one, you can use the `fal deploy` command.

```bash
fal deploy --auth private
```

### Machine Types

You can specify the machine type of your app using the `machine_type` parameter in your `fal.App` class.

For GPU machines, you can also specify the number of GPUs you want to use with the `num_gpus` option.

```python
class MyApp(fal.App):
    machine_type = "GPU-A100"
    num_gpus = 1
    ...
```

Or you may specify the machine type in the `fal deploy` command.

```bash
fal deploy --machine-type GPU-A100 --num-gpus 1
```

#### Machine Type Options

| Value | Description |
|-------|-------------|
| XS | 0.50 CPU cores, 512MB RAM |
| S | 1 CPU core, 1GB RAM (default) |
| M | 2 CPU cores, 2GB RAM |
| L | 4 CPU cores, 15GB RAM |
| GPU-A6000 | 10 CPU cores, 18GB RAM, 1 GPU core (48GB VRAM) |
| GPU-A100 | 12 CPU cores, 60GB RAM, 1 GPU core (40GB VRAM) |
| GPU-H100 | 12 CPU cores, 112GB RAM, 1 GPU core (80GB VRAM) |
| GPU-H200 | 12 CPU cores, 112GB RAM, 1 GPU core (141GB VRAM) |
| GPU-B200 | 24 CPU cores, 112GB RAM, 1 GPU core (192GB VRAM) |

#### Multiple Machine Types

Allow your app to use multiple machine types for a larger pool of available machines:

```python
class MyApp(fal.App):
    machine_type = ["GPU-A100-40G", "GPU-A100-80G"]
```

### Rollout Strategies

Your app could be deployed using one of two strategies:

- **`recreate`**: default, instantly switch the app to the new revision.
- **`rolling`**: doesn't switch the app to the new one until there is at least 1 runner in the new revision.

You can specify the strategy using the `--strategy` flag, e.g.

```bash
fal deploy --strategy rolling
```

### Authentication Modes

Your app could be deployed in one of three authentication modes:

- **`private`**: default, your app is visible only to you and/or your team.
- **`shared`**: everyone can see and use your app, the caller pays for usage. This is how all of the apps in our Model Gallery work.
- **`public`**: everyone can see and use your app, the app owner (you) is paying for it.

Use `fal deploy`'s `--auth` flag or `fal.App`'s `app_auth` to specify your app's authentication mode, e.g.

```python
class MyApp(fal.App):
    auth_mode = "shared"
```

```bash
fal deploy --auth shared
```

To change the mode just redeploy the app.

---

## Migrate from Replicate

This guide will help you transition from using Replicate's tools, specifically their Cog tool, to fal's platform. Cog is a tool used to package machine learning models in Docker containers, which simplifies the deployment process.

### Step 1: Generate the Dockerfile with Cog

First, ensure you have Cog installed. If not, follow the instructions on the Cog GitHub page.

Navigate to your project directory and run:

```bash
cog debug > Dockerfile
```

This command will generate a Dockerfile in the root of your project.

### Step 2: Adapt the Dockerfile for fal

With your Dockerfile generated, you might need to make a few modifications to ensure compatibility with fal.

First, we need to extract Python dependencies and install them in the Docker image. We can do this by copying the dependencies from the Cog file to the Docker image. Here's an example of how you can do this:

> **Requirements**
> 
> The following command assumes you have `yq` installed. If not, you can install it using `pip install yq`. Or follow the instructions on the yq GitHub page.
> 
> You might also need to install `jq` if you don't have it installed. e.g. You can install it using `sudo apt-get install jq` if you are using a Debian-based system. Alternatively, check out the jq GitHub page.

```bash
yq -e '.build.python_packages | map(select(. != null and . != "")) | map("'"'"'" + . + "'"'"'") | join(" ")' cog.yaml
```

This will give you a list of Python packages that you can install in your Docker image. Using `RUN pip install ...` in your Dockerfile.

e.g.

```
'torch' 'torchvision' 'torchaudio' 'torchsde' 'einops' 'transformers>=4.25.1' …
```

Alternatively, you can write the contents of the `python_packages` to a `requirements.txt` file and install them in the Dockerfile. See the example in the containerized application page.

Here's a basic example of what your Dockerfile might look like:

> The example Cog project is https://github.com/fofr/cog-comfyui.

```dockerfile
FROM python:3.10.6 as deps
COPY .cog/tmp/build4143857248/cog-0.0.1.dev-py3-none-any.whl /tmp/cog-0.0.1.dev-py3-none-any.whl
RUN --mount=type=cache,target=/root/.cache/pip pip install -t /dep /tmp/cog-0.0.1.dev-py3-none-any.whl
COPY .cog/tmp/build4143857248/requirements.txt /tmp/requirements.txt
 RUN --mount=type=cache,target=/root/.cache/pip pip install -t /dep -r /tmp/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip pip install -t /dep 'torch' 'torchvision' 'torchaudio' 'torchsde' 'einops' 'transformers>=4.25.1' 'safetensors>=0.3.0' 'aiohttp' 'accelerate' 'pyyaml' 'Pillow' 'scipy' 'tqdm' 'psutil' 'spandrel' 'kornia>=0.7.1' 'websocket-client==1.6.3' 'diffusers>=0.25.0' 'albumentations==1.4.3' 'cmake' 'imageio' 'joblib' 'matplotlib' 'pilgram' 'scikit-learn' 'rembg' 'numba' 'pandas' 'numexpr' 'insightface' 'onnx' 'segment-anything' 'piexif' 'ultralytics!=8.0.177' 'timm' 'importlib_metadata' 'opencv-python-headless>=4.0.1.24' 'filelock' 'numpy' 'einops' 'pyyaml' 'scikit-image' 'python-dateutil' 'mediapipe' 'svglib' 'fvcore' 'yapf' 'omegaconf' 'ftfy' 'addict' 'yacs' 'trimesh[easy]' 'librosa' 'color-matcher' 'facexlib'
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib/x86_64-linux-gnu:/usr/local/nvidia/lib64:/usr/local/nvidia/bin
ENV NVIDIA_DRIVER_CAPABILITIES=all
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked set -eux; \
apt-get update -qq && \
apt-get install -qqy --no-install-recommends curl; \
rm -rf /var/lib/apt/lists/*; \
TINI_VERSION=v0.19.0; \
TINI_ARCH="$(dpkg --print-architecture)"; \
curl -sSL -o /sbin/tini "https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini-${TINI_ARCH}"; \
chmod +x /sbin/tini
ENTRYPOINT ["/sbin/tini", "--"]
ENV PATH="/root/.pyenv/shims:/root/.pyenv/bin:$PATH"
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked apt-get update -qq && apt-get install -qqy --no-install-recommends \
  make \
  build-essential \
  libssl-dev \
  zlib1g-dev \
  libbz2-dev \
  libreadline-dev \
  libsqlite3-dev \
  wget \
  curl \
  llvm \
  libncurses5-dev \
  libncursesw5-dev \
  xz-utils \
  tk-dev \
  libffi-dev \
  liblzma-dev \
  git \
  ca-certificates \
  && rm -rf /var/lib/apt/lists/*
RUN curl -s -S -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash && \
  git clone https://github.com/momo-lab/pyenv-install-latest.git "$(pyenv root)"/plugins/pyenv-install-latest && \
  pyenv install-latest "3.10.6" && \
  pyenv global $(pyenv install-latest --print "3.10.6") && \
  pip install "wheel<1"
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked apt-get update -qq && apt-get install -qqy ffmpeg && rm -rf /var/lib/apt/lists/*
RUN --mount=type=bind,from=deps,source=/dep,target=/dep \
    cp -rf /dep/* $(pyenv prefix)/lib/python*/site-packages; \
    cp -rf /dep/bin/* $(pyenv prefix)/bin; \
    pyenv rehash
RUN curl -o /usr/local/bin/pget -L "https://github.com/replicate/pget/releases/download/v0.8.1/pget_linux_x86_64" && chmod +x /usr/local/bin/pget
RUN pip install onnxruntime-gpu --extra-index-url https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-cuda-12/pypi/simple/
 # fal platform will inject the necessary mechanisms to run your application.
WORKDIR /src
EXPOSE 5000
CMD ["python", "-m", "cog.server.http"]
COPY . /src
```

And that's it! 🎉

Ensure all dependencies and paths match your project's requirements.

### Step 3: Deploy on fal

fal supports deploying Docker-based applications easily. Follow these steps to deploy your Docker container on fal:

1. **Create an account on fal**: If you haven't already, sign up at fal.

2. **Create a new project**: In your favorite directory, create a new project and move the Dockerfile into it. Create a new Python file with the following content:

```python
import fal

from fal.container import ContainerImage
from pathlib import Path

PWD = Path(__file__).resolve().parent


class MyApp(
  fal.App,
  kind="container",
  image=ContainerImage.from_dockerfile(f"{PWD}/Dockerfile"),
):
  def setup(self):
    ...

  @fal.endpoint("/")
  def predict(self, input: Input) -> Output:
    # Rest is your imagination.
```

> **Converting your app/server**
> 
> On a serious note, you need to do a little bit of conversion to run your application. But don't get intimidated, it's just a few lines of code. The structure is of cog server and fal apps are similar, so you can easily adapt your application to run on fal.
> 
> You can see details documentation on how to use fal SDK here.
> 
> More information on how to deploy a containerized application can be found here.

### Step 4: Test Your Deployment

Once deployed, ensure that everything is working as expected by accessing your application through the URL provided by fal. Monitor logs and performance to make sure the migration was successful.

### Troubleshooting

If you encounter any issues during the migration, check the following:

- **Dependencies**: Ensure all required dependencies are listed in your `requirements.txt` or equivalent file.
- **Environment Variables and Build Arguments**: Double-check that all necessary environment variables and build arguments are set correctly in your Dockerfile.
- **Logs**: Use the logging features in fal to diagnose any build or runtime issues.

For further assistance, refer to the fal Documentation or reach out to the fal support team.