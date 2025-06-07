# Steganography

Mountains of information lay all around, but some hidden underneath ordinary appearances. But with tools, we can see what the naked eye cannot. Steganography is a must-learn concept for those following the path of cyber security; this project is a tool to learn and add to that arsenal.

### Setup

```powershell
git clone https://github.com/SilentisVox/Steganography
cd Steganography
pip install -r requirements.txt
```

### Usage

###### Extract
```powershell
python steganography.py --extract IMAGE.png [--out-file DATA.bin]
```

###### Implant
```powershell
python steganography.py --implant IMAGE.png --in-file DATA.bin --out-file NEW.png
```

## Brief Explanation

![definition](assets/definition.png)