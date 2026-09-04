import React, { useCallback, useRef, useState } from 'react';
import { UploadCloud, X, FileText, Image as ImageIcon } from 'lucide-react';
import styles from './FileDropZone.module.css';

/**
 * Generic drag-and-drop / click-to-browse file upload zone.
 * Manages local file state; actual upload happens wherever the caller wires
 * onChange into a submit handler. Generalizes the ImageUploadZone pattern
 * from SellYourUnit.jsx to also accept non-image files (e.g. PDF contracts).
 */
const FileDropZone = ({ files, onChange, accept, maxFiles, maxSizeMB, label, hint }) => {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const acceptedTypes = accept.split(',').map((t) => t.trim());

  const addFiles = useCallback(
    (incoming) => {
      const valid = [];
      const errors = [];

      for (const file of incoming) {
        const isAccepted = acceptedTypes.some((type) =>
          type.startsWith('.') ? file.name.toLowerCase().endsWith(type) : file.type === type
        );
        if (!isAccepted) {
          errors.push(`"${file.name}" is not a supported format.`);
          continue;
        }
        if (file.size > maxSizeMB * 1024 * 1024) {
          errors.push(`"${file.name}" exceeds ${maxSizeMB} MB.`);
          continue;
        }
        if (files.length + valid.length >= maxFiles) {
          errors.push(`Maximum ${maxFiles} files allowed.`);
          break;
        }
        valid.push(file);
      }

      if (errors.length) alert(errors.join('\n'));
      if (valid.length) onChange([...files, ...valid]);
    },
    [files, onChange, acceptedTypes, maxFiles, maxSizeMB]
  );

  const removeFile = (index) => onChange(files.filter((_, i) => i !== index));

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    addFiles(Array.from(e.dataTransfer.files));
  };

  const handleInputChange = (e) => {
    addFiles(Array.from(e.target.files));
    e.target.value = '';
  };

  return (
    <div className={styles.zone}>
      <div
        className={`${styles.dropZone} ${dragging ? styles.dropZoneDragging : ''}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
        aria-label={label}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple
          className={styles.hiddenInput}
          onChange={handleInputChange}
        />
        <UploadCloud className={styles.uploadIcon} size={32} />
        <p className={styles.uploadPrimary}>{label}</p>
        {hint && <p className={styles.uploadSecondary}>{hint}</p>}
      </div>

      {files.length > 0 && (
        <ul className={styles.fileList}>
          {files.map((file, index) => (
            <li key={index} className={styles.fileItem}>
              {file.type.startsWith('image/') ? <ImageIcon size={16} /> : <FileText size={16} />}
              <span className={styles.fileName}>{file.name}</span>
              <button
                type="button"
                className={styles.removeBtn}
                onClick={() => removeFile(index)}
                aria-label={`Remove ${file.name}`}
              >
                <X size={14} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default FileDropZone;
