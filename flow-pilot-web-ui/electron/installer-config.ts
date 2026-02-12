/**
 * installer-config.ts
 * =====================
 * Edge vs Development Installation Mode Configuration
 *
 * PURPOSE:
 *   Determines which features are available in the application.
 *   In "development" mode, all features are enabled (training,
 *   augmentation, data prep, etc.). In "edge" mode, only inference,
 *   DOA/Doppler, calibration, and configuration are available.
 *
 * USAGE:
 *   Set the VITE_INSTALL_MODE environment variable before building:
 *     VITE_INSTALL_MODE=edge npm run build     → edge device
 *     VITE_INSTALL_MODE=development npm run build → full suite
 *
 *   This file can also be imported in the Electron main process
 *   or used in preload to pass mode info to the renderer.
 */

export type InstallMode = 'development' | 'edge';

/**
 * Resolve the current installation mode.
 * Priority: ENV var → config file → default.
 */
export const getInstallMode = (): InstallMode => {
    const envMode = process.env.VITE_INSTALL_MODE || process.env.INSTALL_MODE;
    if (envMode === 'edge') return 'edge';
    return 'development';
};

/**
 * Feature flags for each mode.
 *
 * DESIGN NOTE:
 *   We define features as a flat object rather than nested
 *   so the sidebar can simply check `features[key]`.
 */
export interface FeatureFlags {
    /** Full data acquisition (download, YouTube, etc.) */
    dataAcquisition: boolean;
    /** Data homogenisation and class creation */
    dataPreparation: boolean;
    /** Quality filtering and augmentation */
    filterAugment: boolean;
    /** Model training pipeline */
    training: boolean;
    /** Manual audio filtering UI */
    manualFilter: boolean;
    /** Report generation */
    reports: boolean;
    /** Real-time inference / classification */
    inference: boolean;
    /** DOA estimation */
    doa: boolean;
    /** Doppler velocity analysis */
    doppler: boolean;
    /** Hardware calibration */
    calibration: boolean;
    /** System configuration */
    configuration: boolean;
    /** Admin panel */
    admin: boolean;
}

const DEVELOPMENT_FEATURES: FeatureFlags = {
    dataAcquisition: true,
    dataPreparation: true,
    filterAugment: true,
    training: true,
    manualFilter: true,
    reports: true,
    inference: true,
    doa: true,
    doppler: true,
    calibration: true,
    configuration: true,
    admin: true,
};

const EDGE_FEATURES: FeatureFlags = {
    dataAcquisition: false,
    dataPreparation: false,
    filterAugment: false,
    training: false,
    manualFilter: false,
    reports: false,
    inference: true,
    doa: true,
    doppler: true,
    calibration: true,
    configuration: true,
    admin: true,
};

export const getFeatureFlags = (mode?: InstallMode): FeatureFlags => {
    const m = mode ?? getInstallMode();
    return m === 'edge' ? { ...EDGE_FEATURES } : { ...DEVELOPMENT_FEATURES };
};
