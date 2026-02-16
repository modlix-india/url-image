FROM mcr.microsoft.com/playwright:v1.49.1-noble

RUN apt-get update && apt-get install -y \
    openjdk-21-jdk \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY target/urlscreenshot-1.0.0.jar urlscreenshot-1.0.0.jar

ENV INSTANCE_ID=default

# Reduce glibc memory arena fragmentation (major savings for multi-threaded native code like WebKit)
ENV MALLOC_ARENA_MAX=4

EXPOSE 8080

VOLUME [ "/logs", "/tmp/ehcache" ]

ENTRYPOINT ["java", \
    "-Xms256m", "-Xmx512m", \
    "-XX:+UseContainerSupport", \
    "-XX:MaxMetaspaceSize=128m", \
    "-XX:MaxDirectMemorySize=128m", \
    "-XX:+ExitOnOutOfMemoryError", \
    "-Dserver.tomcat.threads.max=4", \
    "-Dlogging.file.name=/logs/ehcache-${INSTANCE_ID}.log", \
    "-jar", "urlscreenshot-1.0.0.jar"]