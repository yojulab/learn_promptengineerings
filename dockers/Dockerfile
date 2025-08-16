FROM node:24.2-bookworm

# Install necessary tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    openssh-client \
    nano fonts-nanum \
    && rm -rf /var/lib/apt/lists/*

# Set bash as default shell
SHELL ["/bin/bash", "-c"]

# Set working directory
WORKDIR /apps

# Arguments for GitHub credentials
ARG GITHUB_PAT
ENV GITHUB_PAT=${GITHUB_PAT}

# Clone the private repository using PAT
RUN git clone https://github.com/yojulab/learn_promptengineerings.git learn_promptengineerings

WORKDIR /apps/learn_promptengineerings

# Install dependencies and build the application
RUN npm install

# Set environment variables
# ENV JWT_SECRET_KEY="test-your-secret-key-change-in-production"
# ENV JWT_ALGORITHM=HS256
# ENV JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Command to run the application
ENV PORT=3005
# CMD ["npm", "run", "start"]
CMD ["npm", "run", "dev"]
