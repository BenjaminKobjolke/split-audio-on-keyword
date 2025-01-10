import torch
import sys
import platform

def check_cuda():
    print("System Information:")
    print(f"Python version: {sys.version}")
    print(f"PyTorch version: {torch.__version__}")
    print(f"Operating System: {platform.system()} {platform.release()}")
    
    print("\nCUDA Information:")
    cuda_available = torch.cuda.is_available()
    print(f"CUDA available: {cuda_available}")
    
    if cuda_available:
        print(f"CUDA version: {torch.version.cuda}")
        print(f"GPU device: {torch.cuda.get_device_name(0)}")
        print(f"Number of GPUs: {torch.cuda.device_count()}")
        
        # Show memory info for each GPU
        for i in range(torch.cuda.device_count()):
            print(f"\nGPU {i} Memory Info:")
            print(f"Device: {torch.cuda.get_device_name(i)}")
            memory = torch.cuda.get_device_properties(i).total_memory / 1024**3  # Convert to GB
            print(f"Total memory: {memory:.2f} GB")
    else:
        print("No CUDA-capable GPU found")

if __name__ == "__main__":
    check_cuda()
