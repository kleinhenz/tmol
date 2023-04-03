# syntax=docker/dockerfile:1
FROM nvidia/cuda:11.8.0-devel-ubuntu20.04 as base

# general environment for docker
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update; apt-get install -y --no-install-recommends sudo wget curl git vim rsync && rm -rf /var/lib/apt/lists/*

ENV CONDA_DIR=/opt/conda
ENV PATH ${CONDA_DIR}/bin:$PATH

RUN curl -LO https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-x86_64.sh \
  && bash Mambaforge-Linux-x86_64.sh -b -p $CONDA_DIR \
  && rm Mambaforge-Linux-x86_64.sh \
  && conda clean -afy \
  && printf "source ${CONDA_DIR}/etc/profile.d/conda.sh\nsource ${CONDA_DIR}/etc/profile.d/mamba.sh\nmamba activate base" >> /etc/skel/.bashrc \
  && printf "source ${CONDA_DIR}/etc/profile.d/conda.sh\nsource ${CONDA_DIR}/etc/profile.d/mamba.sh\nmamba activate base" >> ~/.bashrc

# create group for conda install
RUN groupadd conda \
    && chgrp -R conda ${CONDA_DIR} \
    && chmod 770 -R ${CONDA_DIR}

# create docker user
RUN useradd -m -s /bin/bash docker && echo "docker:docker" | chpasswd && adduser docker sudo && adduser docker conda

# enable passwordless sudo
RUN echo "docker ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/docker

USER    docker
WORKDIR /home/docker

# FIXME needed for newer versions of sparse but should be replaced by explicit casts to dense where needed
ENV SPARSE_AUTO_DENSIFY 1

FROM base as builder

# NOTE we copy requirements over first so layers are cached and we don't have
# to reinstall dependencies if only source has changed

### NOTE Dependencies can be isntalled in two different ways

### 1. install a fresh environment by re-resolving dependencies based on specification in env.yml and requirements{-dev}.in ###

#COPY --chown=docker requirements.in env.yml /home/docker/tmol/
#RUN mamba env update -n base -f /home/docker/tmol/env.yml
#COPY --chown=docker requirements-dev.in /home/docker/tmol/
#RUN pip install -r /home/docker/tmol/requirements-dev.in

### 2. install a frozen environment with exact versions specified from env.dev.export.yml ###

# we choose (2) here by default for reproducibility
COPY --chown=docker env.dev.export.yml /home/docker/tmol/
RUN mamba env update -n base -f /home/docker/tmol/env.dev.export.yml

COPY --chown=docker . /home/docker/tmol
RUN pip install -e /home/docker/tmol