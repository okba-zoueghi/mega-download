# Use Ubuntu 24.10 as the base image
FROM ubuntu:24.10

# Update and install necessary packages (wget, sudo, git, python3, pip, etc.)
RUN apt-get update && apt-get install -y \
    wget \
    sudo \
    curl \
    vim \
    build-essential \
    dpkg \
    git \
    python3 \
    python3-pip \
    && apt-get clean

# Download and install megacmd
RUN wget https://mega.nz/linux/repo/xUbuntu_24.10/amd64/megacmd-xUbuntu_24.10_amd64.deb && \
    sudo apt install -y ./megacmd-xUbuntu_24.10_amd64.deb && \
    rm megacmd-xUbuntu_24.10_amd64.deb

# Clone the GitHub repository with submodules
RUN git clone --recurse-submodules https://github.com/okba-zoueghi/mega-download.git

# Install Python dependencies from requirements.txt
WORKDIR /mega-download
RUN pip3 install --break-system-packages -r requirements.txt

# Set the default command
CMD ["bash"]
