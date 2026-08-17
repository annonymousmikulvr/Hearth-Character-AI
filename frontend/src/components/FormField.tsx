import type { ReactNode } from "react";

interface FormFieldProps {
  label: string;
  description?: string;
  example?: string;
  hint?: string; // e.g. "Min 0 · Max 2 · Default 0.85"
  required?: boolean;
  children: ReactNode;
}

/**
 * Shared form field with label, description, example, and range/default hint.
 */
export function FormField({
  label,
  description,
  example,
  hint,
  required,
  children,
}: FormFieldProps) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-slate-200 mb-0.5 block">
        {label}
        {required && <span className="text-red-400 ml-0.5">*</span>}
      </span>
      {description && (
        <span className="text-xs text-slate-400 block mb-1">{description}</span>
      )}
      {children}
      <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-1">
        {hint && (
          <span className="text-xs text-slate-500">{hint}</span>
        )}
        {example && (
          <span className="text-xs text-slate-500">
            Example: <span className="text-slate-400 italic">{example}</span>
          </span>
        )}
      </div>
    </label>
  );
}

/** Shared input class used across editors */
export const inputClass =
  "w-full bg-surface-950 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-accent";
