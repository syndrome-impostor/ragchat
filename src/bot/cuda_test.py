import torch

def run_gpu_tests():
    """Run basic PyTorch tests."""
    print("\n=== GPU Test Results ===")
    
    # Test GPU availability
    cuda_available = torch.cuda.is_available()
    print("\nGPU Detection:")
    print(f"CUDA/ROCm available: {cuda_available}")
    
    if cuda_available:
        print(f"Device name: {torch.cuda.get_device_name(0)}")
        print(f"Device count: {torch.cuda.device_count()}")
        
        # Test tensor operations on GPU
        print("\nTensor Test:")
        try:
            x = torch.rand(5, 3)
            print("Testing tensor on CPU:")
            print(f"{x}")
            
            print("\nMoving tensor to GPU...")
            x = torch.rand(5, 3).cuda()
            print(f"{x}")
            print(f"Tensor device: {x.device}")
            
        except Exception as e:
            print(f"Error: Tensor test failed: {str(e)}")
    else:
        print("\nNo GPU detected - checking alternatives:")
        print(f"MPS (Apple Silicon) available: {getattr(torch.backends, 'mps', False) and torch.backends.mps.is_available()}")
        print(f"ROCm available: {hasattr(torch, 'hip') and torch.hip.is_available()}")

if __name__ == "__main__":
    run_gpu_tests()
