// tryon.js
export let liveTryOn = null;
export let currentTryOnItems = [];

export function showTryOnOptions(category = "men's clothing", color = null, max_price = null) {
    const url = new URL("/find_clothing", window.location.origin);
    if (category) url.searchParams.append("category", category);
    if (color) url.searchParams.append("color", color);
    if (max_price) url.searchParams.append("max_price", max_price);

    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.error || data.message) {
                console.warn("No matching items or user not logged in:", data);
                return;
            }

            currentTryOnItems = data;
            const container = document.getElementById("product-options");
            container.innerHTML = "";

            data.forEach((item, index) => {
                const card = document.createElement("div");
                card.className = "product-card";
                card.innerHTML = `
                    <img src="${item.image_url}" alt="product-${index}" />
                    <span><strong>Option ${index + 1}</strong></span>
                    <span>${item.title}</span>
                    <span>${item.price} lei</span>
                `;
                container.appendChild(card);
            });

            toggleWidgetsVisibility(true, false);

            setTimeout(() => {
                const tryOnOptions = document.getElementById('tryon-options');
                if (tryOnOptions.style.display === 'block') {
                    toggleWidgetsVisibility(false, false);
                    console.log("Auto-hide: try-on options removed after 30s.");
                }
            }, 30000);
        })
        .catch(error => console.error("Error loading try-on options:", error));
}

export function toggleWidgetsVisibility(showOptions, showPreview) {
    const widgets = ['weather', 'news', 'crypto', 'calendar'];
    const shouldHide = showOptions || showPreview;

    widgets.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = shouldHide ? 'none' : 'flex';
    });

    const optionsEl = document.getElementById('tryon-options');
    if (optionsEl) optionsEl.style.display = showOptions ? 'block' : 'none';

    const previewEl = document.getElementById('tryon-preview');
    if (previewEl) {
        previewEl.style.display = showPreview ? 'block' : 'none';
        if (showPreview && !liveTryOn) {
            liveTryOn = new LiveTryOn();
            window.liveTryOn = liveTryOn;
        } else if (!showPreview && liveTryOn) {
            liveTryOn.stop();
            liveTryOn = null;
            window.liveTryOn = null;
        }
    }
}

export class LiveTryOn {
    constructor() {
        this.videoElement = document.getElementById("webcam");
        this.canvasElement = document.getElementById("live-canvas");
        this.canvasCtx = this.canvasElement.getContext("2d");
        this.overlayImage = new Image();
        this.overlayImage.style.display = 'none';
        this.timeoutId = null;

        this.pose = new Pose({
            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`,
        });

        this.pose.setOptions({
            modelComplexity: 1,
            smoothLandmarks: true,
            enableSegmentation: false,
            minDetectionConfidence: 0.5,
            minTrackingConfidence: 0.5,
        });

        this.pose.onResults(this.onPoseResults.bind(this));

        this.camera = new Camera(this.videoElement, {
            onFrame: async () => {
                await this.pose.send({ image: this.videoElement });
            },
            width: 640,
            height: 480,
        });

        this.camera.start();
        this.startCloseTimer();
        console.log("Live Try-On session started.");
    }

    startCloseTimer() {
        if (this.timeoutId) clearTimeout(this.timeoutId);
        this.timeoutId = setTimeout(() => {
            console.log("Auto-close after 20s of inactivity.");
            toggleWidgetsVisibility(false, false);
        }, 20000);
    }

    setOverlay(imageUrl) {
        if (imageUrl) {
            this.overlayImage.src = imageUrl;
            this.overlayImage.style.display = 'block';
            this.startCloseTimer();
        } else {
            this.overlayImage.src = '';
            this.overlayImage.style.display = 'none';
        }
    }

    onPoseResults(results) {
        this.canvasCtx.save();
        this.canvasCtx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);
        this.canvasCtx.drawImage(results.image, 0, 0, this.canvasElement.width, this.canvasElement.height);

        if (results.poseLandmarks && this.overlayImage.src) {
            this.drawOverlay(results.poseLandmarks);
        }

        this.canvasCtx.restore();
    }

    drawOverlay(landmarks) {
        const [lS, rS, lH, rH] = [landmarks[11], landmarks[12], landmarks[23], landmarks[24]];
        if ([lS, rS, lH, rH].some(pt => pt.visibility < 0.7)) return;

        const w = this.canvasElement.width;
        const h = this.canvasElement.height;

        const x = (lS.x + rS.x) / 2;
        const y = (lS.y + rH.y) / 2;
        const torsoWidth = Math.abs(lS.x - rS.x) * w * 1.8;
        const torsoHeight = Math.abs(lS.y - lH.y) * h * 1.1;
        const angle = Math.atan2(rS.y - lS.y, rS.x - lS.x) + Math.PI;

        this.canvasCtx.save();
        this.canvasCtx.translate(x * w, y * h);
        this.canvasCtx.rotate(angle);
        this.canvasCtx.drawImage(this.overlayImage, -torsoWidth / 2, -torsoHeight / 2, torsoWidth, torsoHeight);
        this.canvasCtx.restore();
    }

    stop() {
        if (this.timeoutId) clearTimeout(this.timeoutId);
        this.camera.stop();
        this.pose.close();
        console.log("Live Try-On stopped.");
    }
}
