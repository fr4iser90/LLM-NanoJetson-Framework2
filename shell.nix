{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    # Python and core dependencies
    python311
    python311Packages.pip
    python311Packages.pyyaml
    python311Packages.pytest
    
    # LLM and AI utilities
    python311Packages.transformers
    python311Packages.torch
    python311Packages.sentencepiece
    python311Packages.huggingface-hub
    
    # Networking and communication
    python311Packages.fastapi
    python311Packages.uvicorn
    python311Packages.requests
    python311Packages.websockets
    
    # Development tools
    python311Packages.black
    python311Packages.mypy
    python311Packages.pylint
    
    # Utility packages
    python311Packages.ipython
    python311Packages.jupyter
    python311Packages.tqdm
    python311Packages.numpy
    python311Packages.matplotlib
    
    # System integration
    python311Packages.psutil
    python311Packages.paramiko  # For SSH to Nano
  ];

  shellHook = ''
    # Create virtual environment if it doesn't exist
    if [ ! -d .venv ]; then
      python -m venv .venv
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Setup PYTHONPATH to include our framework
    export PYTHONPATH=$PWD:$PYTHONPATH
    
    # Create project structure if it doesn't exist
    if [ ! -d "src" ]; then
      mkdir -p src/{agents,models,utils,config}
      mkdir -p tests
      touch src/__init__.py
      touch src/agents/__init__.py
      touch src/models/__init__.py
      touch src/utils/__init__.py
      
      echo "Project structure created!"
    fi
    
    # Print welcome message
    echo "AutoCoder Development Environment Ready!"
    echo "Python version: $(python --version)"
    echo "Pip version: $(pip --version)"
    echo ""
    echo "To start a new project:"
    echo "python autocoder.py --prompt \"Your project idea\""
  '';
}
