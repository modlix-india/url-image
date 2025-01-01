package com.modlix.urlscreenshot.enums;

public enum ImageSizeType {

    THUMB(320, 180),
    THUMBX2(640, 320),
    ORIGINAL(0, 0),
    FULL(0, 0),
    FULLXHALF(0, 0);

    ImageSizeType(int width, int height) {
        this.width = width;
        this.height = height;
    }

    private final int width;
    private final int height;

    public int getWidth() {
        return width;
    }

    public int getHeight() {
        return height;
    }
}
