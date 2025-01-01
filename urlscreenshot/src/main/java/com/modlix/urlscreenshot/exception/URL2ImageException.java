package com.modlix.urlscreenshot.exception;

import java.io.Serial;

public class URL2ImageException extends RuntimeException {

    @Serial
    private static final long serialVersionUID = 1L;

    public URL2ImageException(String message) {
        super(message);
    }

    public URL2ImageException(String message, Throwable cause) {
        super(message, cause);
    }

}
