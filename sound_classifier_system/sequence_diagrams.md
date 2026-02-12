# Acoustic AI — Sequence Diagrams

Mermaid sequence diagrams showing how each backend service is triggered from the frontend.

---

## 1. Audio Acquisition (Hardware → WebSocket → Frontend)

```mermaid
sequenceDiagram
    participant U as User
    participant FE as React Frontend
    participant WS as WebSocket /ws/stream/{id}
    participant HAL as HAL Layer
    participant MIC as Microphone/Sensor

    U->>FE: Click "Start Streaming"
    FE->>WS: Connect WebSocket
    WS->>HAL: open(device_id, sr=44100)
    HAL->>MIC: Start capture
    loop Every ~100ms
        MIC->>HAL: Raw PCM frames
        HAL->>WS: float32 audio bytes
        WS->>WS: extract_features(audio)
        WS->>FE: JSON {features_length, message}
        FE->>FE: Update LiveMonitor
    end
    U->>FE: Click "Stop"
    FE->>WS: Close WebSocket
    WS->>HAL: close()
```

---

## 2. Feature Extraction (File Upload → API → Response)

```mermaid
sequenceDiagram
    participant U as User
    participant FE as React Frontend
    participant API as POST /api/processing/extract-features
    participant FX as feature_extraction.py

    U->>FE: Upload audio file
    FE->>API: FormData {file, config_json}
    API->>API: Save to temp file
    API->>FX: extract_features(tmp_path, config)
    FX->>FX: librosa.load → MFCC + Chroma + Mel + Spectral
    FX-->>API: numpy array (193 features)
    API-->>FE: JSON {features: [...], length: 193}
    FE->>FE: Display feature summary
```

---

## 3. DOA Analysis (Multi-Channel Upload → GCC-PHAT → Angle)

```mermaid
sequenceDiagram
    participant U as User
    participant FE as React Frontend
    participant API as POST /api/analysis/doa
    participant DOA as doa.py

    U->>FE: Upload multi-channel audio
    FE->>API: FormData {file, mic_distance, channel_a, channel_b}
    API->>API: librosa.load(mono=False) → 2D array
    API->>DOA: gcc_phat(sig1, sig2, sr, max_tau)
    DOA->>DOA: FFT cross-correlation → peak delay τ
    DOA-->>API: τ (seconds)
    API->>DOA: estimate_doa(sig1, sig2, sr, mic_dist)
    DOA->>DOA: θ = arcsin(τ × v_sound / d)
    DOA-->>API: angle_deg
    API-->>FE: JSON {angle_deg, tdoa_seconds, sample_rate}
    FE->>FE: Render DOA compass indicator
```

---

## 4. Doppler Analysis (Upload → FFT Frequency Track → Velocity)

```mermaid
sequenceDiagram
    participant U as User
    participant FE as DopplerAnalysis.tsx
    participant API as POST /api/analysis/doppler
    participant DP as doppler.py

    U->>FE: Upload audio + set speed_of_sound
    FE->>API: FormData {file, config_json}
    API->>DP: full_doppler_analysis(audio, sr, params)
    DP->>DP: frequency_track(audio, sr)
    loop Each frame (100ms hop)
        DP->>DP: dominant_frequency(frame) via FFT + parabolic interp
    end
    DP->>DP: calculate_velocity(f_observed, f_source, v_sound)
    DP->>DP: Classify direction: approaching / receding / stationary
    DP-->>API: {times, frequencies, velocities, directions, summary}
    API-->>FE: Full Doppler result JSON
    FE->>FE: Render velocity card + direction badge
```

---

## 5. Hybrid Classification (Frequency Bands + Doppler → First Guess)

```mermaid
sequenceDiagram
    participant U as User
    participant FE as DopplerAnalysis.tsx
    participant API as POST /api/analysis/hybrid-classify
    participant FF as frequency_filter.py
    participant DP as doppler.py

    U->>FE: Upload audio
    FE->>API: FormData {file, config_json}
    API->>DP: full_doppler_analysis(audio, sr)
    DP-->>API: doppler_result {summary: {velocity, direction}}
    API->>FF: hybrid_classify(audio, sr, doppler_result)
    FF->>FF: frequency_band_energy(audio, sr)
    FF->>FF: Match bands to known sound signatures
    FF->>FF: Boost confidence if Doppler confirms motion
    FF-->>API: {first_guess, candidates, band_energies, is_moving}
    API-->>FE: Hybrid result + doppler_summary
    FE->>FE: Render classification card + band table
```

---

## 6. Data Homogenisation (Frontend Trigger → File Copy Pipeline)

```mermaid
sequenceDiagram
    participant U as User
    participant FE as React Frontend
    participant API as POST /api/data/homogenise
    participant MBC as metadata_based_class_creation.py
    participant FS as Filesystem

    U->>FE: Configure base_path, output_path, metadata_file
    FE->>API: JSON {base_path, output_path, metadata_file}
    API->>MBC: homogenise_dataset(base_path, output_path, metadata_file)
    MBC->>MBC: Auto-detect CSV columns (filename, class)
    MBC->>FS: Scan for audio files (.wav/.mp3/.flac/.ogg)
    loop Each row in metadata CSV
        MBC->>FS: Copy file → output_path/<class>/<file>
        Note over MBC: Skip if destination exists (idempotent)
    end
    MBC-->>API: {class_name: file_count, ...}
    API-->>FE: JSON {status, classes, total_files}
    FE->>FE: Show success notification
```

---

## 7. Filter + Augment Pipeline

```mermaid
sequenceDiagram
    participant U as User
    participant FE as React Frontend
    participant API as POST /api/data/filter-augment
    participant FA as filtering_augmentation.py
    participant FS as Filesystem

    U->>FE: Set filter thresholds + augment targets
    FE->>API: JSON {input_dir, filtered_dir, augmented_dir, ...}
    
    rect rgb(230, 245, 255)
        Note over API,FA: Stage 1: Quality Filter
        API->>FA: filter_dataset(input_dir, filtered_dir, config)
        loop Each class directory
            loop Each audio file
                FA->>FA: Check duration, RMS, bandpass, SNR
                alt Passes all checks
                    FA->>FS: Copy to filtered_dir/<class>/
                else Fails
                    FA->>FA: Log rejection reason
                end
            end
        end
        FA-->>API: filter_report {passed, rejected, reasons}
    end
    
    rect rgb(230, 255, 230)
        Note over API,FA: Stage 2: Balanced Augmentation
        API->>FA: augment_dataset(filtered_dir, augmented_dir, config)
        loop Each class with < target samples
            FA->>FA: Pitch shift / time-stretch / noise inject
            FA->>FS: Write augmented files
        end
        FA-->>API: augment_report {per_class_counts}
    end
    
    API-->>FE: JSON {filter_report, augment_report}
```

---

## 8. Model Training (Feature Folder → sklearn → Model Artifact)

```mermaid
sequenceDiagram
    participant U as User
    participant FE as React Frontend
    participant API as POST /api/model/train
    participant SK as scikit-learn

    U->>FE: Select data_path, model_type, feature_config
    FE->>API: JSON TrainRequest
    API->>API: Load .pkl feature files from features/
    API->>SK: train_test_split(X, y, stratify=y)
    API->>SK: StandardScaler.fit_transform(X_train)
    
    alt model_type == "random_forest"
        API->>SK: RandomForestClassifier(n=100)
    else model_type == "svm"
        API->>SK: SVC(kernel=rbf, probability=True)
    else model_type == "knn"
        API->>SK: KNeighborsClassifier(n=5)
    end
    
    SK->>SK: clf.fit(X_train, y_train)
    SK->>SK: clf.predict(X_test) → accuracy
    API->>API: joblib.dump → models/model_{id}.joblib
    API-->>FE: JSON {model_id, accuracy, classification_report}
    FE->>FE: Show accuracy & per-class metrics
```

---

## 9. Real-time Classification (WebSocket Stream)

```mermaid
sequenceDiagram
    participant U as User
    participant FE as LiveMonitor.tsx
    participant WS as WS /ws/stream/{sensor_id}
    participant FX as feature_extraction.py
    participant ML as joblib model

    U->>FE: Select sensor, click "Start"
    FE->>WS: WebSocket connect
    
    loop Continuous audio stream
        FE->>WS: Raw float32 audio bytes
        WS->>WS: np.frombuffer → audio array
        WS->>FX: extract_features(temp_wav)
        FX-->>WS: feature vector
        
        alt Model loaded
            WS->>ML: clf.predict(features)
            ML-->>WS: prediction + confidence
            WS->>FE: JSON {prediction, confidence, sensor_id}
        else No model
            WS->>FE: JSON {message: "Features extracted, no model"}
        end
        
        FE->>FE: Update classification panel
    end
    
    U->>FE: Click "Stop"
    FE->>WS: Close
```

---

## 10. Spectrogram / Waveform Visualisation

```mermaid
sequenceDiagram
    participant U as User
    participant FE as React Frontend
    participant API as POST /api/visualize/spectrogram
    participant MPL as matplotlib

    U->>FE: Upload audio file
    FE->>API: FormData {file, n_fft=2048, hop_length=512}
    API->>API: librosa.load(tmp_path)
    API->>MPL: melspectrogram → power_to_db
    MPL->>MPL: specshow + colorbar
    MPL->>MPL: fig.savefig(buf, format=png, dpi=100)
    MPL-->>API: BytesIO PNG buffer
    API->>API: base64.b64encode(buf)
    API-->>FE: JSON {image_base64, content_type: "image/png"}
    FE->>FE: <img src="data:image/png;base64,...">
```

---

## 11. Doppler Visualisation Plot

```mermaid
sequenceDiagram
    participant U as User
    participant FE as DopplerAnalysis.tsx
    participant API as POST /api/visualize/doppler
    participant DP as doppler.py
    participant FF as frequency_filter.py
    participant MPL as matplotlib

    U->>FE: Click "Run Analysis"
    FE->>API: FormData {file, config_json}
    API->>DP: full_doppler_analysis(audio, sr)
    DP-->>API: {times, frequencies, velocities, directions}
    API->>FF: frequency_band_energy(audio, sr)
    FF-->>API: [{name, energy, ...}]
    
    API->>MPL: Create 3-subplot figure
    Note over MPL: 1. Freq vs Time line plot
    Note over MPL: 2. Velocity bar chart (green/red)
    Note over MPL: 3. Band energy horizontal bars
    MPL->>MPL: savefig → Base64 PNG
    API-->>FE: JSON {image_base64, doppler_summary}
    FE->>FE: Render plot image + summary cards
```

---

## 12. Anomaly Detection (Ambient vs Threat)

```mermaid
sequenceDiagram
    participant U as User
    participant FE as applicationService.ts
    participant API as POST /api/m5-application/anomaly-detection
    participant AM as application_models.py

    U->>FE: Submit feature matrix + method
    FE->>API: JSON {features, method, contamination}
    API->>AM: detect_anomalies(X, method, contamination)
    AM->>AM: StandardScaler.fit_transform(X)
    alt method == "isolation_forest"
        AM->>AM: IsolationForest(n_estimators=200)
    else method == "one_class_svm"
        AM->>AM: OneClassSVM(kernel=rbf)
    end
    AM->>AM: model.fit(X_scaled)
    AM->>AM: labels = model.predict(X_scaled)
    AM->>AM: scores = model.decision_function(X_scaled)
    AM->>AM: joblib.dump → anomaly model saved
    AM-->>API: {anomalies, scores, labels, stats}
    API-->>FE: Full anomaly result JSON
    FE->>FE: Highlight anomalous samples
```

---

## 13. Audio Clustering (Unsupervised Labelling)

```mermaid
sequenceDiagram
    participant U as User
    participant FE as applicationService.ts
    participant API as POST /api/m5-application/clustering
    participant AM as application_models.py

    U->>FE: Submit features + method + n_clusters
    FE->>API: JSON {features, method, n_clusters, parameters}
    API->>AM: cluster_audio(X, method, n_clusters)
    AM->>AM: StandardScaler.fit_transform(X)
    alt method == "kmeans"
        AM->>AM: KMeans(n_clusters).fit_predict(X)
    else method == "dbscan"
        AM->>AM: DBSCAN(eps, min_samples).fit_predict(X)
    else method == "hierarchical"
        AM->>AM: AgglomerativeClustering.fit_predict(X)
    end
    AM->>AM: silhouette_score(X, labels)
    AM-->>API: {cluster_labels, centers, silhouette, sizes}
    API-->>FE: Cluster result JSON
    FE->>FE: Display clusters for labelling
```

---

## 14. Audio Chunking (Click/Silence Split)

```mermaid
sequenceDiagram
    participant U as User
    participant FE as preprocessingService.ts
    participant API as POST /api/data/chunk-audio
    participant GC as generate_chunks.py
    participant FS as Filesystem

    U->>FE: Set input_dir, output_dir
    FE->>API: JSON {input_dir, output_dir}
    API->>GC: process_all_files(input_dir, output_dir)
    loop Each audio file
        GC->>GC: Detect click boundaries
        GC->>FS: Write segments to output_dir
    end
    GC-->>API: Complete
    API->>API: Count output files
    API-->>FE: JSON {status, files_created}
```

---

## 15. Dataset Split (Train/Val/Test)

```mermaid
sequenceDiagram
    participant U as User
    participant FE as dataAcquisitionService.ts
    participant API as POST /api/data/organize-splits
    participant OS as organize_sound_samples.py
    participant FS as Filesystem

    U->>FE: Set input_dir, output_dir, split ratios
    FE->>API: JSON {input_dir, output_dir, test_size, val_size}
    API->>OS: organize_samples(input, output, splits)
    OS->>OS: Scan class directories
    OS->>OS: Stratified train_test_split (sklearn)
    loop Each split (train, val, test)
        OS->>FS: Copy files to output/<split>/<class>/
    end
    OS-->>API: Complete
    API->>API: Count files per split
    API-->>FE: JSON {status, splits: {train: N, val: N, test: N}}
```

---

## 16. Source Separation (NMF)

```mermaid
sequenceDiagram
    participant U as User
    participant FE as preprocessingService.ts
    participant API as POST /api/processing/source-separation
    participant SS as source_separation.py

    U->>FE: Upload mixed audio + n_components
    FE->>API: FormData {file, n_components}
    API->>API: librosa.load(tmp_path)
    API->>SS: separate_sources(audio, n_components)
    SS->>SS: librosa.stft → magnitude spectrogram
    SS->>SS: NMF(n_components).fit_transform
    SS->>SS: Reconstruct each source via istft
    SS-->>API: list[ndarray] — separated sources
    API->>API: Encode each source → WAV → Base64
    API-->>FE: JSON {n_sources, sources: [{audio_base64, ...}]}
    FE->>FE: Render playable audio for each source
```

---

## 17. Admin Panel – Backend Process Management

```mermaid
sequenceDiagram
    participant U as User
    participant FE as AdminPanel.tsx
    participant IPC as Electron IPC
    participant EP as Electron Main Process
    participant PY as Python FastAPI

    U->>FE: Click "Start Backend"
    FE->>IPC: backend:start {port: 8000}
    IPC->>EP: spawn("python", ["-m", "api.main"])
    EP->>PY: Process starts
    EP-->>IPC: {pid, status: "running"}
    IPC-->>FE: Update status indicator (green)
    
    loop Health polling (every 5s)
        FE->>PY: GET /api/health
        PY-->>FE: {status: "ok"}
        FE->>FE: Green indicator + uptime
    end
    
    U->>FE: Click "Stop Backend"
    FE->>IPC: backend:stop
    IPC->>EP: process.kill(pid)
    EP-->>IPC: {status: "stopped"}
    IPC-->>FE: Update status indicator (red)
```
