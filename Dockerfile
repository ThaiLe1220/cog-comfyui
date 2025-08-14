#syntax=docker/dockerfile:1.4
FROM r8.im/cog-base:cuda12.1-python3.12-torch2.5.1
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked apt-get update -qq && apt-get install -qqy  && rm -rf /var/lib/apt/lists/*
ENV R8_COG_VERSION=coglet
ENV R8_PYTHON_VERSION=3.12
RUN pip install https://github.com/replicate/cog-runtime/releases/download/v0.1.0-beta7/coglet-0.1.0b7-py3-none-any.whl
COPY .cog/tmp/build20250813193453.998124/requirements.txt /tmp/requirements.txt
ENV CFLAGS="-O3 -funroll-loops -fno-strict-aliasing -flto -S"
RUN --mount=type=cache,target=/root/.cache/pip pip install -r /tmp/requirements.txt
ENV CFLAGS=
RUN curl -o /usr/local/bin/pget -L "https://github.com/replicate/pget/releases/latest/download/pget_$(uname -s)_$(uname -m)" && chmod +x /usr/local/bin/pget
RUN pip install onnxruntime-gpu --extra-index-url https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-cuda-12/pypi/simple/
WORKDIR /src
EXPOSE 5000
CMD ["python", "-m", "cog.server.http"]
COPY . /src
