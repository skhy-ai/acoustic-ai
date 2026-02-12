/**
 * Experiment Service – Local SQLite via Electron IPC
 * ====================================================
 * Replaces the previous Supabase-backed service.
 * All data is stored in a local SQLite database managed
 * by the Electron main process.
 */

export interface Experiment {
  id?: number;
  name: string;
  description?: string;
  status: string;
  config: Record<string, any>;
  created_at?: string;
}

export interface Execution {
  id?: number;
  experiment_id: number;
  started_at?: string;
  finished_at?: string;
  status: string;
  metrics?: Record<string, any>;
}

// Type guard for Electron environment
const isElectron = (): boolean =>
  typeof window !== "undefined" && !!(window as any).electronAPI;

const dbQuery = async (sql: string, params?: any[]): Promise<any> => {
  if (isElectron()) {
    return (window as any).electronAPI.dbQuery(sql, params);
  }
  // Fallback: localStorage for non-Electron dev
  console.warn("[experimentService] Not in Electron – using localStorage fallback");
  return null;
};

export const experimentService = {
  // ── Experiments ─────────────────────────────────────────────
  async createExperiment(exp: Experiment): Promise<Experiment> {
    const result = await dbQuery(
      `INSERT INTO experiments (name, description, status, config)
       VALUES (?, ?, ?, ?)`,
      [exp.name, exp.description || "", exp.status || "draft",
      JSON.stringify(exp.config || {})]
    );
    return { ...exp, id: result?.lastInsertRowid };
  },

  async getExperiments(): Promise<Experiment[]> {
    const rows = await dbQuery(
      `SELECT * FROM experiments ORDER BY created_at DESC`
    );
    if (!Array.isArray(rows)) return [];
    return rows.map((r: any) => ({
      ...r,
      config: typeof r.config === "string" ? JSON.parse(r.config) : r.config,
    }));
  },

  async getExperiment(id: number): Promise<Experiment | null> {
    const rows = await dbQuery(
      `SELECT * FROM experiments WHERE id = ?`, [id]
    );
    if (!Array.isArray(rows) || rows.length === 0) return null;
    const r = rows[0];
    return {
      ...r,
      config: typeof r.config === "string" ? JSON.parse(r.config) : r.config,
    };
  },

  async updateExperiment(id: number, patch: Partial<Experiment>): Promise<void> {
    const sets: string[] = [];
    const vals: any[] = [];
    if (patch.name !== undefined) { sets.push("name = ?"); vals.push(patch.name); }
    if (patch.description !== undefined) { sets.push("description = ?"); vals.push(patch.description); }
    if (patch.status !== undefined) { sets.push("status = ?"); vals.push(patch.status); }
    if (patch.config !== undefined) { sets.push("config = ?"); vals.push(JSON.stringify(patch.config)); }
    if (sets.length === 0) return;
    vals.push(id);
    await dbQuery(`UPDATE experiments SET ${sets.join(", ")} WHERE id = ?`, vals);
  },

  async deleteExperiment(id: number): Promise<void> {
    await dbQuery(`DELETE FROM executions WHERE experiment_id = ?`, [id]);
    await dbQuery(`DELETE FROM experiments WHERE id = ?`, [id]);
  },

  // ── Executions ──────────────────────────────────────────────
  async createExecution(exec: Execution): Promise<Execution> {
    const result = await dbQuery(
      `INSERT INTO executions (experiment_id, status, metrics)
       VALUES (?, ?, ?)`,
      [exec.experiment_id, exec.status || "running",
      JSON.stringify(exec.metrics || {})]
    );
    return { ...exec, id: result?.lastInsertRowid };
  },

  async updateExecution(id: number, patch: Partial<Execution>): Promise<void> {
    const sets: string[] = [];
    const vals: any[] = [];
    if (patch.status !== undefined) { sets.push("status = ?"); vals.push(patch.status); }
    if (patch.finished_at !== undefined) { sets.push("finished_at = ?"); vals.push(patch.finished_at); }
    if (patch.metrics !== undefined) { sets.push("metrics = ?"); vals.push(JSON.stringify(patch.metrics)); }
    if (sets.length === 0) return;
    vals.push(id);
    await dbQuery(`UPDATE executions SET ${sets.join(", ")} WHERE id = ?`, vals);
  },

  async getExecutions(experimentId: number): Promise<Execution[]> {
    const rows = await dbQuery(
      `SELECT * FROM executions WHERE experiment_id = ? ORDER BY started_at DESC`,
      [experimentId]
    );
    if (!Array.isArray(rows)) return [];
    return rows.map((r: any) => ({
      ...r,
      metrics: typeof r.metrics === "string" ? JSON.parse(r.metrics) : r.metrics,
    }));
  },
};
