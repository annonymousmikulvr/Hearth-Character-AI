import { api } from "./client";
import type { SetupStatus } from "../types";

export const setupApi = {
  status: () => api.get<SetupStatus>("/setup"),
  create: (data_root: string) =>
    api.post<SetupStatus>("/setup", { data_root, create_new: true }),
  open: (data_root: string) =>
    api.post<SetupStatus>("/setup/open", { data_root, create_new: false }),
};
