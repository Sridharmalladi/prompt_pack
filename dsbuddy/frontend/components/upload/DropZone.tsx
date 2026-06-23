"use client";

import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { cn } from "@/lib/utils";
import { FileIcon, XIcon } from "lucide-react";

const ACCEPTED_TYPES: Record<string, string[]> = {
  "text/csv": [".csv"],
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
  "application/vnd.ms-excel": [".xls"],
  "application/octet-stream": [".parquet"],
};

const MAX_SIZE_BYTES = 100 * 1024 * 1024;

interface DropZoneProps {
  file: File | null;
  onFileSelect: (file: File) => void;
  onFileClear: () => void;
  disabled?: boolean;
}

export function DropZone({ file, onFileSelect, onFileClear, disabled = false }: DropZoneProps) {
  const onDrop = useCallback(
    (accepted: File[]) => { if (accepted[0]) onFileSelect(accepted[0]); },
    [onFileSelect]
  );

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxFiles: 1,
    maxSize: MAX_SIZE_BYTES,
    disabled,
  });

  const rejectionMessage = fileRejections[0]?.errors[0]?.message;

  if (file) {
    return (
      <div className="flex items-center justify-between rounded border border-border bg-card px-3.5 py-2.5">
        <div className="flex items-center gap-2.5 min-w-0">
          <FileIcon className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          <div className="min-w-0">
            <p className="text-xs font-medium truncate text-foreground">{file.name}</p>
            <p className="text-[10px] text-muted-foreground">
              {(file.size / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>
        </div>
        {!disabled && (
          <button
            type="button"
            onClick={onFileClear}
            className="shrink-0 ml-3 text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Remove file"
          >
            <XIcon className="h-3.5 w-3.5" />
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      <div
        {...getRootProps()}
        className={cn(
          "rounded border border-dashed px-6 py-10 text-center cursor-pointer transition-all",
          isDragActive
            ? "border-foreground/40 bg-secondary"
            : "border-border/70 hover:border-foreground/30 hover:bg-secondary/50",
          disabled && "pointer-events-none opacity-40"
        )}
      >
        <input {...getInputProps()} />
        <p className="text-sm text-muted-foreground">
          {isDragActive
            ? "Drop it here"
            : <><span className="text-foreground font-medium">Drop your file here</span>{" "}or{" "}<span className="underline underline-offset-2 text-foreground/70">browse</span></>
          }
        </p>
        <p className="mt-1 text-[10px] text-muted-foreground/70">CSV, XLSX, Parquet · max 100 MB</p>
      </div>
      {rejectionMessage && (
        <p className="text-[11px] text-destructive">{rejectionMessage}</p>
      )}
    </div>
  );
}
