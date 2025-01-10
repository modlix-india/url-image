package com.modlix.urlscreenshot.service;

import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.Image;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;

import javax.imageio.ImageIO;

import org.springframework.stereotype.Service;

import com.modlix.urlscreenshot.enums.ImageType;

@Service
public class ImageService {

    public byte[] resizeImage(byte[] sc, ImageType imageType, Integer imageWidth,
            Integer imageHeight,
            String imageBandColor) throws IOException {

        ByteArrayInputStream bis = new ByteArrayInputStream(sc);
        BufferedImage bi = ImageIO.read(bis);

        if (imageWidth != 0 && imageHeight != 0) {
            bi = resize(bi, imageType, imageWidth, imageHeight, imageBandColor);
        }

        ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
        ImageIO.write(bi, imageType.toString().toLowerCase(), byteArrayOutputStream);

        return byteArrayOutputStream.toByteArray();
    }

    private BufferedImage resize(BufferedImage bi, ImageType imageType, Integer imageWidth, Integer imageHeight,
            String imageBandColor) {
        BufferedImage endBI = new BufferedImage(imageWidth, imageHeight,
                imageType == ImageType.JPEG ? BufferedImage.TYPE_INT_RGB : BufferedImage.TYPE_INT_ARGB);

        Graphics2D g = endBI.createGraphics();

        if (imageType == ImageType.JPEG || (imageBandColor != null && !imageBandColor.isBlank())) {
            if (imageBandColor == null || imageBandColor.isBlank())
                g.setColor(Color.BLACK);
            else
                g.setColor(decodeFromHEXtoColor(imageBandColor));

            g.fillRect(0, 0, imageWidth, imageHeight);
        }

        int x = 0;
        int y = 0;

        int newWidth;
        int newHeight;

        float widthRatio = (float) imageWidth / bi.getWidth();
        float heightRatio = (float) imageHeight / bi.getHeight();

        if (widthRatio < heightRatio) {
            newWidth = imageWidth;
            newHeight = (int) (bi.getHeight() * widthRatio);
            y = (imageHeight - newHeight) / 2;
        } else {
            newHeight = imageHeight;
            newWidth = (int) (bi.getWidth() * heightRatio);
            x = (imageWidth - newWidth) / 2;
        }

        g.drawImage(bi.getScaledInstance(newWidth, newHeight, Image.SCALE_SMOOTH), x, y, null);

        return endBI;
    }

    private Color decodeFromHEXtoColor(String hex) {

        int start = 0;
        if (hex.startsWith("#")) {
            start = 1;
        }

        int bit4Or8 = hex.length() - start > 4 ? 2 : 1;

        int r = Integer.parseInt(hex.substring(start, start + bit4Or8), 16);
        start += bit4Or8;
        int g = Integer.parseInt(hex.substring(start, start + bit4Or8), 16);
        start += bit4Or8;
        int b = Integer.parseInt(hex.substring(start, start + bit4Or8), 16);
        start += bit4Or8;

        int a = bit4Or8 == 2 ? 255 : 15;

        if (start < hex.length()) {
            a = Integer.parseInt(hex.substring(start, start + bit4Or8), 16);
        }

        if (bit4Or8 == 1) {
            r = r << 4 | r;
            g = g << 4 | g;
            b = b << 4 | b;
            a = a << 4 | a;
        }

        return new Color(r, g, b, a);

    }
}
