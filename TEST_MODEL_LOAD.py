"""
Test Script - Testet ob ein Modell geladen werden kann
Hilft herauszufinden welcher Modellname für 'lms load' funktioniert
"""

import subprocess
import sys

def test_model_load(model_name):
    """Testet ob ein Modell geladen werden kann"""
    
    print("=" * 70)
    print(f"Testing: lms load {model_name}")
    print("=" * 70)
    
    # Test 1: Unload all
    print("\n[1] Unloading all models...")
    try:
        result = subprocess.run(
            ['lms', 'unload', '--all', '-y'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("✓ Unload successful")
        else:
            print(f"⚠ Unload returned code {result.returncode}")
    except Exception as e:
        print(f"✗ Unload failed: {e}")
    
    # Test 2: Load model
    print(f"\n[2] Loading model: {model_name}")
    try:
        cmd = ['lms', 'load', model_name, '-y', '--context-length=8192', '--gpu=1']
        print(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print(f"Return code: {result.returncode}")
        
        if result.stdout:
            print(f"\nStdout:\n{result.stdout}")
        
        if result.stderr:
            print(f"\nStderr:\n{result.stderr}")
        
        if result.returncode == 0:
            print("\n✓ Load successful!")
        else:
            print("\n✗ Load failed!")
            
    except subprocess.TimeoutExpired:
        print("\n✗ Timeout (>60s)")
    except Exception as e:
        print(f"\n✗ Error: {e}")
    
    # Test 3: Check if loaded
    print(f"\n[3] Checking if model is loaded...")
    try:
        result = subprocess.run(
            ['lms', 'ps'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        print(f"\nCurrently loaded models:")
        print(result.stdout)
        
        if model_name in result.stdout:
            print(f"✓ Model found in 'lms ps' output")
        else:
            print(f"✗ Model NOT found in 'lms ps' output")
            print(f"   Maybe it's using a different name?")
            
    except Exception as e:
        print(f"✗ Error checking: {e}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        model_name = sys.argv[1]
    else:
        print("Usage: python TEST_MODEL_LOAD.py <model-name>")
        print("\nExample:")
        print("  python TEST_MODEL_LOAD.py google/gemma-3-27b")
        print("  python TEST_MODEL_LOAD.py llava-v1.5-7b")
        print("\nOr run 'lms ls --detailed' to see available models")
        sys.exit(1)
    
    test_model_load(model_name)
