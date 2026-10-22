/**
 * LEO-COORD Photorealistic 3D Digital Globe Engine
 * Sử dụng Three.js WebGL với ảnh vệ tinh NASA Blue Marble độ phân giải cao thực tế.
 * Tích hợp:
 * - Quả địa cầu 3D với lớp ảnh vệ tinh NASA thực tế, khí quyển phát sáng
 * - Vùng lãnh thổ & 3 trạm mặt đất Việt Nam (Hà Nội, Đà Nẵng, TP.HCM)
 * - Chòm sao Walker LEO 120 vệ tinh 3D chuyển động thực tế kèm búp sóng
 * - Vệ tinh Địa tĩnh GSO Vinasat-1/2 và Cung phối hợp +-6 độ
 * - Thước đo cự ly Slant Range & Góc ngẩng laser 3D
 * - Điều khiển OrbitControls: xoay tự do mọi góc nhìn, zoom mượt mà
 */

class LeoGlobe3D {
    constructor(canvasId) {
        this.container = document.querySelector('.canvas-wrapper');
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas || !this.container) return;

        // Trạng thái mô phỏng
        this.simTime = 0;
        this.simSpeed = 10;
        this.isPlaying = true;
        this.earthRadius = 100;
        this.altKm = 550;
        this.incDeg = 53;
        this.nSats = 120;
        this.nPlanes = 6;
        this.footprintRadiusKm = 1657;

        // Lớp dữ liệu (GIS Layers)
        this.showOrbits = true;
        this.showFootprints = true;
        this.showBeams = true;
        this.showLabels = true;
        this.showGso = true;
        this.showSlantRange = true;

        this.selectedSat = null;
        this.satellitesData = [];
        this.orbitPlanesData = [];

        // Khởi tạo Three.js
        this.initThree();
        this.initLights();
        this.initEarth();
        this.initAtmosphere();
        this.initStarfield();
        this.initGroundStations();
        this.initGsoRingAndVinasat();
        this.initSatellites();
        this.initSlantRangeLaser();

        this.initEvents();
        this.animate();
        this.fetchOrbitData();

        // Mặc định xoay camera về phía Việt Nam
        setTimeout(() => this.focusVietnam(), 300);
    }

    initThree() {
        const width = this.container.clientWidth || 800;
        const height = this.container.clientHeight || 560;

        // Scene
        this.scene = new THREE.Scene();

        // Camera
        this.camera = new THREE.PerspectiveCamera(45, width / height, 1, 3000);
        this.camera.position.set(0, 50, 260);

        // Renderer
        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            antialias: true,
            alpha: true,
            powerPreference: "high-performance"
        });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

        // OrbitControls
        if (typeof THREE.OrbitControls !== 'undefined') {
            this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
            this.controls.enableDamping = true;
            this.controls.dampingFactor = 0.05;
            this.controls.minDistance = 120;
            this.controls.maxDistance = 700;
            this.controls.enablePan = true;
            if (typeof THREE.TOUCH !== 'undefined') {
                this.controls.touches = {
                    ONE: THREE.TOUCH.ROTATE,
                    TWO: THREE.TOUCH.DOLLY_PAN
                };
            }
        }
    }

    initLights() {
        // Ánh sáng môi trường dịu nhẹ
        const ambientLight = new THREE.AmbientLight(0x384152, 0.85);
        this.scene.add(ambientLight);

        // Mặt Trời chiếu sáng tạo vùng ngày/đêm thực tế
        this.sunLight = new THREE.DirectionalLight(0xffffff, 1.4);
        this.sunLight.position.set(300, 100, 200);
        this.scene.add(this.sunLight);

        // Ánh sáng phản xạ thứ cấp phía tối
        const backLight = new THREE.DirectionalLight(0x0e7490, 0.4);
        backLight.position.set(-300, -50, -200);
        this.scene.add(backLight);
    }

    initEarth() {
        const R = this.earthRadius;
        const geometry = new THREE.SphereGeometry(R, 64, 64);

        // Nạp ảnh vệ tinh NASA Blue Marble thực tế
        const textureLoader = new THREE.TextureLoader();
        const earthTexture = textureLoader.load(
            '/static/assets/earth_day.jpg',
            () => { this.renderer.render(this.scene, this.camera); },
            undefined,
            (err) => { console.warn("Lỗi nạp texture ảnh vệ tinh:", err); }
        );

        const material = new THREE.MeshPhongMaterial({
            map: earthTexture,
            specular: new THREE.Color(0x223344),
            shininess: 12,
            bumpScale: 0.05
        });

        this.earthMesh = new THREE.Mesh(geometry, material);
        this.scene.add(this.earthMesh);
    }

    initAtmosphere() {
        // Lớp khí quyển phát quang màu xanh dương mờ ảo
        const R = this.earthRadius * 1.018;
        const geometry = new THREE.SphereGeometry(R, 48, 48);
        const material = new THREE.MeshBasicMaterial({
            color: 0x38bdf8,
            transparent: true,
            opacity: 0.12,
            side: THREE.BackSide,
            blending: THREE.AdditiveBlending
        });
        this.atmosphereMesh = new THREE.Mesh(geometry, material);
        this.scene.add(this.atmosphereMesh);
    }

    initStarfield() {
        // Bầu trời 2.000 vì sao không gian sâu
        const starGeo = new THREE.BufferGeometry();
        const starCount = 2000;
        const starPos = new Float32Array(starCount * 3);

        for (let i = 0; i < starCount * 3; i += 3) {
            const rad = 600 + Math.random() * 800;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos((Math.random() * 2) - 1);
            starPos[i] = rad * Math.sin(phi) * Math.cos(theta);
            starPos[i + 1] = rad * Math.sin(phi) * Math.sin(theta);
            starPos[i + 2] = rad * Math.cos(phi);
        }

        starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
        const starMat = new THREE.PointsMaterial({
            color: 0xffffff,
            size: 1.5,
            transparent: true,
            opacity: 0.8
        });
        const stars = new THREE.Points(starGeo, starMat);
        this.scene.add(stars);
    }

    // Chuyển đổi vĩ độ, kinh độ sang tọa độ 3D chuẩn khớp với texture NASA Blue Marble
    latLonToVector3(lat, lon, radius) {
        const phi = (90 - lat) * (Math.PI / 180);
        const theta = (lon + 180) * (Math.PI / 180);
        const x = -(radius * Math.sin(phi) * Math.cos(theta));
        const z = radius * Math.sin(phi) * Math.sin(theta);
        const y = radius * Math.cos(phi);
        return new THREE.Vector3(x, y, z);
    }

    initGroundStations() {
        this.groundStationGroup = new THREE.Group();
        this.stations = [
            { id: "hanoi", name: "Hà Nội (Trạm Bắc)", lat: 21.0285, lon: 105.8542, color: 0x38bdf8 },
            { id: "danang", name: "Đà Nẵng (Trạm Trung)", lat: 16.0544, lon: 108.2022, color: 0x34d399 },
            { id: "hcmc", name: "TP. Hồ Chí Minh (Trạm Nam)", lat: 10.8231, lon: 106.6297, color: 0xfbbf24 }
        ];

        this.pulseRings = [];

        this.stations.forEach(st => {
            const pos = this.latLonToVector3(st.lat, st.lon, this.earthRadius);

            // Điểm ghim 3D
            const pinGeo = new THREE.SphereGeometry(1.5, 16, 16);
            const pinMat = new THREE.MeshBasicMaterial({ color: st.color });
            const pinMesh = new THREE.Mesh(pinGeo, pinMat);
            pinMesh.position.copy(pos);
            this.groundStationGroup.add(pinMesh);

            // Cột định vị hướng ra ngoài
            const normal = pos.clone().normalize();
            const poleGeo = new THREE.CylinderGeometry(0.3, 0.3, 4, 8);
            const poleMat = new THREE.MeshBasicMaterial({ color: st.color });
            const pole = new THREE.Mesh(poleGeo, poleMat);
            pole.position.copy(pos.clone().add(normal.clone().multiplyScalar(2)));
            pole.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), normal);
            this.groundStationGroup.add(pole);

            // Vòng radar phát xung nhịp
            const ringGeo = new THREE.RingGeometry(2, 3, 24);
            const ringMat = new THREE.MeshBasicMaterial({
                color: st.color,
                transparent: true,
                opacity: 0.6,
                side: THREE.DoubleSide
            });
            const ring = new THREE.Mesh(ringGeo, ringMat);
            ring.position.copy(pos.clone().add(normal.clone().multiplyScalar(0.2)));
            ring.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), normal);
            this.groundStationGroup.add(ring);

            this.pulseRings.push({ mesh: ring, baseScale: 1.0 });
        });

        this.scene.add(this.groundStationGroup);
    }

    initGsoRingAndVinasat() {
        this.gsoGroup = new THREE.Group();
        const gsoVisualR = this.earthRadius * 2.15; // Tỷ lệ trực quan vành đai địa tĩnh

        // 1. Vòng xích đạo địa tĩnh GSO (Geostationary Ring)
        const gsoRingPts = [];
        for (let l = -180; l <= 180; l += 3) {
            gsoRingPts.push(this.latLonToVector3(0, l, gsoVisualR));
        }
        const gsoRingGeo = new THREE.BufferGeometry().setFromPoints(gsoRingPts);
        const gsoRingMat = new THREE.LineDashedMaterial({
            color: 0xec4899,
            dashSize: 3,
            gapSize: 2,
            transparent: true,
            opacity: 0.4
        });
        const gsoLine = new THREE.Line(gsoRingGeo, gsoRingMat);
        gsoLine.computeLineDistances();
        this.gsoGroup.add(gsoLine);

        // 2. Vệ tinh Vinasat-1 (132°E) & Vinasat-2 (105.5°E) kèm Cung phối hợp +-6 độ
        const vinasats = [
            { name: "VINASAT-1", lon: 132.0, color: 0xf43f5e },
            { name: "VINASAT-2", lon: 105.5, color: 0xec4899 }
        ];

        vinasats.forEach(v => {
            const pos = this.latLonToVector3(0, v.lon, gsoVisualR);

            // Thân vệ tinh Vinasat hình thoi bát diện (Octahedron)
            const satGeo = new THREE.OctahedronGeometry(2.8, 0);
            const satMat = new THREE.MeshBasicMaterial({ color: v.color });
            const satMesh = new THREE.Mesh(satGeo, satMat);
            satMesh.position.copy(pos);
            this.gsoGroup.add(satMesh);

            // Búp sóng chiếu về Việt Nam
            const vnCenter = this.latLonToVector3(16.0, v.lon, this.earthRadius);
            const beamPts = [pos, vnCenter];
            const beamGeo = new THREE.BufferGeometry().setFromPoints(beamPts);
            const beamMat = new THREE.LineBasicMaterial({
                color: v.color,
                transparent: true,
                opacity: 0.25
            });
            this.gsoGroup.add(new THREE.Line(beamGeo, beamMat));

            // Dải Cung phối hợp +-6 độ
            const arcPts = [];
            for (let al = v.lon - 6; al <= v.lon + 6; al += 0.5) {
                arcPts.push(this.latLonToVector3(0, al, gsoVisualR));
            }
            const arcGeo = new THREE.BufferGeometry().setFromPoints(arcPts);
            const arcMat = new THREE.LineBasicMaterial({ color: 0xf43f5e, linewidth: 3 });
            this.gsoGroup.add(new THREE.Line(arcGeo, arcMat));
        });

        this.scene.add(this.gsoGroup);
    }

    initSatellites() {
        this.leoGroup = new THREE.Group();
        this.orbitLineGroup = new THREE.Group();
        this.footprintGroup = new THREE.Group();

        this.leoGroup.add(this.orbitLineGroup);
        this.leoGroup.add(this.footprintGroup);
        this.scene.add(this.leoGroup);

        this.satMeshes = [];
        this.coneMeshes = [];
        this.rebuildOrbitLines();
    }

    rebuildOrbitLines() {
        // Xóa các đường cũ
        while (this.orbitLineGroup.children.length > 0) {
            this.orbitLineGroup.remove(this.orbitLineGroup.children[0]);
        }

        const satR = this.earthRadius * (1 + this.altKm / 6378.137);
        const spread = 360.0;

        for (let p = 0; p < this.nPlanes; p++) {
            const raan = (p * spread / this.nPlanes) * Math.PI / 180;
            const inc = this.incDeg * Math.PI / 180;
            const pts = [];

            for (let theta = 0; theta <= Math.PI * 2; theta += 0.08) {
                const x_orb = Math.cos(theta);
                const y_orb = Math.sin(theta);
                const x = (x_orb * Math.cos(raan) - y_orb * Math.cos(inc) * Math.sin(raan)) * satR;
                const y = (y_orb * Math.sin(inc)) * satR;
                const z = (x_orb * Math.sin(raan) + y_orb * Math.cos(inc) * Math.cos(raan)) * satR;
                pts.push(new THREE.Vector3(x, y, z));
            }

            const geo = new THREE.BufferGeometry().setFromPoints(pts);
            const mat = new THREE.LineBasicMaterial({
                color: 0x0284c7,
                transparent: true,
                opacity: 0.35
            });
            this.orbitLineGroup.add(new THREE.Line(geo, mat));
        }
    }

    initSlantRangeLaser() {
        // Tia laser 3D từ trạm Đà Nẵng lên vệ tinh LEO gần nhất
        const pts = [new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 0, 0)];
        const geo = new THREE.BufferGeometry().setFromPoints(pts);
        const mat = new THREE.LineDashedMaterial({
            color: 0x38bdf8,
            dashSize: 3,
            gapSize: 2,
            linewidth: 2
        });
        this.laserLine = new THREE.Line(geo, mat);
        this.scene.add(this.laserLine);
    }

    updateSatellitesPositions() {
        const satR = this.earthRadius * (1 + this.altKm / 6378.137);
        const satsPerPlane = Math.floor(this.nSats / this.nPlanes);

        // Khởi tạo mesh nếu số lượng thay đổi
        if (this.satMeshes.length !== this.nSats) {
            this.satMeshes.forEach(m => this.leoGroup.remove(m));
            this.coneMeshes.forEach(c => this.footprintGroup.remove(c));
            this.satMeshes = [];
            this.coneMeshes = [];

            for (let i = 0; i < this.nSats; i++) {
                // Thân vệ tinh LEO
                const satObj = new THREE.Group();
                const bodyGeo = new THREE.BoxGeometry(1.2, 1.2, 1.6);
                const bodyMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });
                satObj.add(new THREE.Mesh(bodyGeo, bodyMat));

                // Cánh pin năng lượng mặt trời 2 bên
                const wingGeo = new THREE.BoxGeometry(4.5, 0.1, 1.0);
                const wingMat = new THREE.MeshBasicMaterial({ color: 0x0284c7 });
                satObj.add(new THREE.Mesh(wingGeo, wingMat));

                this.leoGroup.add(satObj);
                this.satMeshes.push(satObj);

                // Nón búp sóng phủ chiếu xuống Trái Đất (Downlink Footprint)
                const coneGeo = new THREE.ConeGeometry(8, satR - this.earthRadius, 16, 1, true);
                const coneMat = new THREE.MeshBasicMaterial({
                    color: 0x06b6d4,
                    transparent: true,
                    opacity: 0.08,
                    side: THREE.DoubleSide
                });
                const cone = new THREE.Mesh(coneGeo, coneMat);
                this.footprintGroup.add(cone);
                this.coneMeshes.push(cone);
            }
        }

        // Cập nhật tọa độ từng vệ tinh theo thời gian simTime
        let idx = 0;
        let nearestSatPos = null;
        let minDist = Infinity;
        const daNangPos = this.latLonToVector3(16.0544, 108.2022, this.earthRadius);

        for (let p = 0; p < this.nPlanes; p++) {
            const raan = (p * (360.0 / this.nPlanes)) * Math.PI / 180;
            const inc = this.incDeg * Math.PI / 180;

            for (let s = 0; s < satsPerPlane; s++) {
                if (idx >= this.nSats) break;

                const u = ((360.0 / satsPerPlane) * s + (this.simTime * 0.15)) * Math.PI / 180;
                const x_orb = Math.cos(u);
                const y_orb = Math.sin(u);

                const x = (x_orb * Math.cos(raan) - y_orb * Math.cos(inc) * Math.sin(raan)) * satR;
                const y = (y_orb * Math.sin(inc)) * satR;
                const z = (x_orb * Math.sin(raan) + y_orb * Math.cos(inc) * Math.cos(raan)) * satR;
                const pos = new THREE.Vector3(x, y, z);

                const mesh = this.satMeshes[idx];
                mesh.position.copy(pos);
                mesh.lookAt(0, 0, 0);

                // Tính kinh/vĩ độ để phát hiện can nhiễu vào Cung phối hợp Vinasat (+-6 độ quanh 105.5°E và 132°E)
                const lat = Math.asin(y / satR) * (180 / Math.PI);
                const lon = Math.atan2(z, -x) * (180 / Math.PI) - 180;
                const inCoordArc = (Math.abs(lon - 105.5) <= 6.0 && Math.abs(lat) <= 15.0) ||
                                   (Math.abs(lon - 132.0) <= 6.0 && Math.abs(lat) <= 15.0);

                // Đổi màu vệ tinh thành đỏ nếu vi phạm cung phối hợp
                mesh.children[0].material.color.setHex(inCoordArc ? 0xf43f5e : 0x38bdf8);

                // Cập nhật nón búp sóng
                const cone = this.coneMeshes[idx];
                cone.visible = this.showFootprints;
                if (this.showFootprints) {
                    const subPoint = pos.clone().normalize().multiplyScalar(this.earthRadius);
                    const midPoint = pos.clone().add(subPoint).multiplyScalar(0.5);
                    cone.position.copy(midPoint);
                    cone.quaternion.setFromUnitVectors(new THREE.Vector3(0, -1, 0), pos.clone().normalize());
                    cone.material.color.setHex(inCoordArc ? 0xf43f5e : 0x06b6d4);
                }

                // Tìm vệ tinh gần Đà Nẵng nhất để đo cự ly
                const dist = pos.distanceTo(daNangPos);
                if (dist < minDist) {
                    minDist = dist;
                    nearestSatPos = pos;
                }

                idx++;
            }
        }

        // Cập nhật thước đo Laser Slant Range
        if (this.showSlantRange && nearestSatPos) {
            this.laserLine.visible = true;
            const pts = [daNangPos, nearestSatPos];
            this.laserLine.geometry.setFromPoints(pts);
            this.laserLine.computeLineDistances();

            // Tính cự ly xiên thực tế
            const realSlant = Math.round(minDist * (6378.137 / this.earthRadius));
            const elDeg = Math.round(Math.max(10, 90 - (minDist / satR) * 60));
            if (window.updateSlantHUD) {
                window.updateSlantHUD(realSlant, elDeg);
            }
        } else {
            this.laserLine.visible = false;
        }
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        if (this.isPlaying) {
            this.simTime = (this.simTime + (1 / 60) * this.simSpeed) % 86400;
            if (window.updateTimelineUI) {
                window.updateTimelineUI(this.simTime);
            }
        }

        // Xung nhịp radar trạm mặt đất
        const pulse = (Math.sin(this.simTime * 6) + 1) * 0.4 + 0.8;
        this.pulseRings.forEach(p => {
            p.mesh.scale.set(pulse, pulse, 1);
        });

        // Hiệu ứng nhịp phát sáng cho vệ tinh thực tế N2YO
        if (this.realSatBeaconRing) {
            const satPulse = (Math.sin(Date.now() * 0.006) + 1) * 0.35 + 0.8;
            this.realSatBeaconRing.scale.set(satPulse, satPulse, 1);
        }
        if (this.realSatMarker) {
            this.realSatMarker.rotation.y += 0.03;
            this.realSatMarker.rotation.x += 0.015;
        }

        // Bật/tắt các lớp theo cài đặt UI
        this.orbitLineGroup.visible = this.showOrbits;
        this.gsoGroup.visible = this.showGso;
        this.groundStationGroup.visible = this.showLabels;

        // Cập nhật vị trí vệ tinh
        this.updateSatellitesPositions();

        // Cập nhật camera controls
        if (this.controls) this.controls.update();

        this.renderer.render(this.scene, this.camera);
    }

    resize() {
        if (!this.container || !this.renderer || !this.camera) return;
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        if (width === 0 || height === 0) return;
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    initEvents() {
        window.addEventListener('resize', () => this.resize());
        window.addEventListener('orientationchange', () => {
            setTimeout(() => this.resize(), 150);
        });
    }

    focusVietnam() {
        // Hướng camera thẳng vào tọa độ Việt Nam (210° lon tương ứng trên texture)
        const targetPos = new THREE.Vector3(-140, 60, 160);
        this.animateCameraTo(targetPos, new THREE.Vector3(0, 0, 0));
    }

    focusGso() {
        // Zoom xa để quan sát toàn bộ quỹ đạo địa tĩnh 35.786km
        const targetPos = new THREE.Vector3(0, 150, 480);
        this.animateCameraTo(targetPos, new THREE.Vector3(0, 0, 0));
    }

    animateCameraTo(targetPosition, targetLookAt) {
        const lookTarget = targetLookAt || new THREE.Vector3(0, 0, 0);
        if (!this.controls) {
            this.camera.position.copy(targetPosition);
            this.camera.lookAt(lookTarget);
            return;
        }

        const startPos = this.camera.position.clone();
        const startTarget = this.controls.target.clone();
        let progress = 0;

        const step = () => {
            progress += 0.05;
            const t = Math.min(progress, 1.0);
            this.camera.position.lerpVectors(startPos, targetPosition, t);
            this.controls.target.lerpVectors(startTarget, lookTarget, t);
            this.controls.update();
            if (progress < 1.0) {
                requestAnimationFrame(step);
            }
        };
        step();
    }

    setConstellationParams(alt, inc, sats, planes) {
        this.altKm = alt;
        this.incDeg = inc;
        this.nSats = sats;
        this.nPlanes = planes;
        this.rebuildOrbitLines();
    }

    setSimTime(seconds) {
        this.simTime = Math.max(0, Math.min(86400, seconds));
    }

    focusRealSatellite(lat, lon, altKm, name) {
        if (!this.realSatGroup) {
            this.realSatGroup = new THREE.Group();
            this.scene.add(this.realSatGroup);
        }
        this.realSatGroup.clear();

        const latNum = parseFloat(lat);
        const lonNum = parseFloat(lon);
        const altNum = parseFloat(altKm) || 550;

        // Tính bán kính trực quan (LEO ~115-130, GSO ~180-220)
        const isGso = altNum > 30000;
        const visualR = isGso ? 190 : this.earthRadius + Math.min(35, Math.max(8, (altNum / 1500) * 20));
        const satPos = this.latLonToVector3(latNum, lonNum, visualR);
        const subPos = this.latLonToVector3(latNum, lonNum, this.earthRadius);

        // Marker vệ tinh (Octahedron phát sáng vàng neon)
        const markerGeo = new THREE.OctahedronGeometry(4.0, 0);
        const markerMat = new THREE.MeshBasicMaterial({ color: 0xffea00 });
        const markerMesh = new THREE.Mesh(markerGeo, markerMat);
        markerMesh.position.copy(satPos);
        this.realSatGroup.add(markerMesh);
        this.realSatMarker = markerMesh;

        // Vòng tròn halo bao quanh vệ tinh
        const ringGeo = new THREE.RingGeometry(5.0, 6.8, 32);
        const ringMat = new THREE.MeshBasicMaterial({ color: 0xffea00, side: THREE.DoubleSide });
        const ringMesh = new THREE.Mesh(ringGeo, ringMat);
        ringMesh.position.copy(satPos);
        ringMesh.lookAt(new THREE.Vector3(0, 0, 0));
        this.realSatGroup.add(ringMesh);
        this.realSatBeaconRing = ringMesh;

        // Tia chiếu thẳng xuống mặt đất (Sub-satellite beam line)
        const beamPts = [satPos, subPos];
        const beamGeo = new THREE.BufferGeometry().setFromPoints(beamPts);
        const beamMat = new THREE.LineDashedMaterial({ color: 0xffea00, dashSize: 3, gapSize: 1.5 });
        const beamLine = new THREE.Line(beamGeo, beamMat);
        beamLine.computeLineDistances();
        this.realSatGroup.add(beamLine);

        // Vòng tròn footprint nhỏ tại vị trí mặt đất (sub-satellite point)
        const subRingGeo = new THREE.RingGeometry(2.0, 3.8, 24);
        const subRingMat = new THREE.MeshBasicMaterial({ color: 0xffea00, side: THREE.DoubleSide });
        const subRingMesh = new THREE.Mesh(subRingGeo, subRingMat);
        subRingMesh.position.copy(subPos.clone().multiplyScalar(1.002));
        subRingMesh.lookAt(new THREE.Vector3(0, 0, 0));
        this.realSatGroup.add(subRingMesh);

        // Tia nối từ vệ tinh tới trạm Đà Nẵng (Đại diện trạm VN)
        const daNangPos = this.latLonToVector3(16.0544, 108.2022, this.earthRadius);
        const slantPts = [satPos, daNangPos];
        const slantGeo = new THREE.BufferGeometry().setFromPoints(slantPts);
        const slantMat = new THREE.LineBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.85 });
        this.realSatGroup.add(new THREE.Line(slantGeo, slantMat));

        // Animate camera tới vệ tinh (nhìn thẳng vào tâm Trái Đất qua vệ tinh)
        const camDist = isGso ? visualR + 120 : visualR + 65;
        const camPos = satPos.clone().normalize().multiplyScalar(camDist);
        this.animateCameraTo(camPos, new THREE.Vector3(0, 0, 0));

        // Cập nhật card chi tiết vệ tinh
        const card = document.getElementById("sat-info-card");
        if (card) {
            card.style.display = "block";
            const idEl = document.getElementById("info-sat-id");
            if (idEl) idEl.textContent = `🎯 [LIVE] ${name || "REAL-SAT"}`;
            const planeEl = document.getElementById("info-sat-plane");
            if (planeEl) planeEl.textContent = isGso ? "Quỹ đạo Địa tĩnh (GSO)" : "Quỹ đạo Thấp LEO (Live N2YO)";
            const coordsEl = document.getElementById("info-sat-coords");
            if (coordsEl) coordsEl.textContent = `${latNum >= 0 ? latNum.toFixed(2) + '°N' : (-latNum).toFixed(2) + '°S'}, ${lonNum >= 0 ? lonNum.toFixed(2) + '°E' : (-lonNum).toFixed(2) + '°W'}`;
            const altEl = document.getElementById("info-sat-alt");
            if (altEl) altEl.textContent = `${Math.round(altNum).toLocaleString()} km`;
        }
    }

    async fetchOrbitData() {
        try {
            const res = await fetch(`/api/orbits/state?alt_km=${this.altKm}&inc_deg=${this.incDeg}&n_sats=${this.nSats}&n_planes=${this.nPlanes}&sim_time_sec=${this.simTime}`);
            if (res.ok) {
                const data = await res.json();
                this.satellitesData = data.satellites || [];
                this.orbitPlanesData = data.orbit_planes || [];
                if (data.footprint_radius_km) this.footprintRadiusKm = data.footprint_radius_km;
            }
        } catch (e) {
            console.error("Lỗi fetch quỹ đạo:", e);
        }
    }
}

window.LeoGlobe3D = LeoGlobe3D;
