import { useState } from "react";
import type { ReactNode } from "react";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
  onConfirm: () => void | Promise<void>;
  onCancel: () => void;
  children?: ReactNode;
}

export default function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  danger = false,
  onConfirm,
  onCancel,
  children,
}: ConfirmDialogProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!open) return null;

  async function handleConfirm() {
    setIsSubmitting(true);
    try {
      await onConfirm();
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="confirm-dialog-backdrop" onClick={onCancel}>
      <div className="confirm-dialog" onClick={(e) => e.stopPropagation()}>
        <div className={`confirm-dialog-icon ${danger ? "danger" : ""}`}>
          {danger ? (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path d="M12 9v4M12 17h.01M10.3 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L14.7 3.86a2 2 0 0 0-3.4 0Z" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          ) : (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path d="M12 8v4l2.5 2.5M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          )}
        </div>
        <h3 className="confirm-dialog-title">{title}</h3>
        <p className="confirm-dialog-message">{message}</p>
        {children}
        <div className="confirm-dialog-actions">
          <button className="secondary-button" onClick={onCancel} disabled={isSubmitting}>
            {cancelLabel}
          </button>
          <button className={danger ? "danger-button" : ""} onClick={handleConfirm} disabled={isSubmitting}>
            {isSubmitting ? "Working..." : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
