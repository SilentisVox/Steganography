## **Steganography**

### **Setup**

```cmd
git clone https://github.com/SilentisVox/Steganography
cd Steganography
python steganography.py
```

### **Usage**

```cmd
python steganography.py --extract IMAGE.png [--out-file DATA.bin]

python steganography.py --implant IMAGE.png --in-file DATA.bin --out-file NEW.png
```

## **Brief Explanation**

![definition](https://github.com/user-attachments/assets/82689ca6-619a-4740-af76-583b8ac62cb1)

### **What is Steganography?**
Steganography is the art of hiding information within non-secret data, such as images, audio, or text, in a way that it remains undetectable to the naked eye. Unlike encryption, which scrambles data to make it unreadable without a key, steganography conceals the very existence of the hidden message.

### **How Does It Work with Images?**
Digital images are made up of tiny squares called **pixels**. Each pixel contains color information represented by four values: **R (Red), G (Green), B (Blue), and A (Alpha/Transparency)**. Each of these values is stored as a **byte** (8 bits), which means we can subtly modify them without changing the way the image looks.

### **Using the Least Significant Bit (LSB)**
A byte consists of 8 bits, where each bit contributes to the overall value. The **Least Significant Bit (LSB)** is the smallest, least important bit in a byte. Since changing it only slightly alters the color, the difference is nearly imperceptible to human eyes.

By encoding secret data into these least significant bits across an image, we can **embed a hidden message** without visibly altering the image. This technique allows for discreet communication or secure data storage in plain sight.

### **Example of LSB Steganography**
1. **Original Pixel (R, G, B, A in binary)**:  
   ```
   Red:   11001100  
   Green: 10111001  
   Blue:  11101011  
   Alpha: 11111111  
   ```
2. **Hidden Data (Binary Message: "1101")**
   - Embed **1** into the LSB of Red
   - Embed **1** into the LSB of Green
   - Embed **0** into the LSB of Blue
   - Embed **1** into the LSB of Alpha

3. **Modified Pixel (with hidden data)**
   ```
   Red:   11001101  (LSB changed)  
   Green: 10111001  (No change)  
   Blue:  11101010  (LSB changed)  
   Alpha: 11111111  (No change)  
   ```

Since these changes are so minor, the image appears unchanged to the human eye while secretly containing data.
