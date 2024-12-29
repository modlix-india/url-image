package com.modlix.urlscreenshot.dto;

import java.io.Serial;
import java.io.Serializable;

import com.modlix.urlscreenshot.enums.DeviceType;
import com.modlix.urlscreenshot.enums.ImageSizeType;
import com.modlix.urlscreenshot.enums.ImageType;

import jakarta.servlet.http.HttpServletRequest;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.ToString;
import lombok.experimental.Accessors;

@Data
@EqualsAndHashCode
@Accessors(chain = true)
@ToString
public class URLImageParameters implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    private DeviceType deviceType = DeviceType.DESKTOP;
    private Integer deviceWidth;
    private Integer deviceHeight;

    private ImageSizeType imageSizeType = ImageSizeType.THUMB;
    private Integer imageWidth;
    private Integer imageHeight;

    private ImageType imageType = ImageType.WEBP;

    private String imageBandColor;
    private String cacheControl = "public, max-age=604800";

    public Integer getDeviceWidth() {
        return deviceWidth == null || deviceWidth == 0 ? deviceType.getWidth() : deviceWidth;
    }

    public Integer getDeviceHeight() {
        return deviceHeight == null || deviceHeight == 0 ? deviceType.getHeight() : deviceHeight;
    }

    public Integer getImageWidth() {
        return imageWidth == null || imageWidth == 0 ? imageSizeType.getWidth() : imageWidth;
    }

    public Integer getImageHeight() {
        return imageHeight == null || imageHeight == 0 ? imageSizeType.getHeight() : imageHeight;
    }

    public static URLImageParameters of(HttpServletRequest request) {

        URLImageParameters parameters = new URLImageParameters();

        String deviceType = request.getParameter("deviceType");
        if (deviceType != null) {
            parameters.setDeviceType(DeviceType.valueOf(deviceType.toUpperCase()));
        }

        String deviceWidth = request.getParameter("deviceWidth");
        if (deviceWidth != null) {
            parameters.setDeviceWidth(Integer.parseInt(deviceWidth));
        }

        String deviceHeight = request.getParameter("deviceHeight");
        if (deviceHeight != null) {
            parameters.setDeviceHeight(Integer.parseInt(deviceHeight));
        }

        String imageSizeType = request.getParameter("imageSizeType");
        if (imageSizeType != null) {
            parameters.setImageSizeType(ImageSizeType.valueOf(imageSizeType.toUpperCase()));
        }

        String imageWidth = request.getParameter("imageWidth");
        if (imageWidth != null) {
            parameters.setImageWidth(Integer.parseInt(imageWidth));
        }

        String imageHeight = request.getParameter("imageHeight");
        if (imageHeight != null) {
            parameters.setImageHeight(Integer.parseInt(imageHeight));
        }

        String imageType = request.getParameter("imageType");
        if (imageType != null) {
            parameters.setImageType(ImageType.valueOf(imageType.toUpperCase()));
        }

        String imageBandColor = request.getParameter("imageBandColor");
        if (imageBandColor != null) {
            parameters.setImageBandColor(imageBandColor);
        }

        String cacheControl = request.getParameter("cacheControl");
        if (cacheControl != null) {
            parameters.setCacheControl(cacheControl);
        }

        return parameters;
    }
}
