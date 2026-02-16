FROM mcr.microsoft.com/playwright:v1.49.1-noble

RUN apt-get update && apt-get install -y \
    openjdk-21-jdk \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY target/urlscreenshot-1.0.0.jar urlscreenshot-1.0.0.jar

ENV INSTANCE_ID=default

EXPOSE 8080

VOLUME [ "/logs", "/tmp/ehcache" ]

ENTRYPOINT ["java", "-Xms256m", "-Xmx512m", "-XX:+UseContainerSupport", "-XX:MaxRAMPercentage=75.0", "-Dlogging.file.name=/logs/ehcache-${INSTANCE_ID}.log", "-jar", "urlscreenshot-1.0.0.jar"]