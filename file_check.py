import os

def list_files(startpath):
    output = []
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        output.append(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            output.append(f"{subindent}{f}")
    return output

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"CURRENT DIRECTORY: {current_dir}")
    print(f"WORKING DIRECTORY: {os.getcwd()}")
    
    files = list_files(current_dir)
    print("\nFILE STRUCTURE:")
    for file in files:
        print(file)
    
    # Check for requirements.txt in multiple locations
    locations = [
        os.path.join(current_dir, 'requirements.txt'),
        os.path.join(os.getcwd(), 'requirements.txt'),
        os.path.join(current_dir, 'src', 'requirements.txt')
    ]
    
    for req_path in locations:
        print(f"\nCHECKING: {req_path}")
        if os.path.exists(req_path):
            print("✅ FILE EXISTS")
            with open(req_path, 'r') as f:
                content = f.read()
                print(f"CONTENT ({len(content)} chars):")
                print(content)
            break
        else:
            print("❌ FILE NOT FOUND")
    
    # List all files with 'requirements' in the name
    print("\nALL FILES WITH 'requirements' IN NAME:")
    for root, dirs, files in os.walk(current_dir):
        for file in files:
            if 'requirements' in file.lower():
                full_path = os.path.join(root, file)
                print(f"FOUND: {full_path}")
