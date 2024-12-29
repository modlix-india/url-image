package com.modlix.urlscreenshot.enums;

public enum ImageType {
    PNG("image/png"),
    JPEG("image/jpeg"),
    WEBP("image/webp");

    private final String contentType;

    ImageType(String type) {
        this.contentType = type;
    }

    public String getContentType() {
        return contentType;
    }
}
