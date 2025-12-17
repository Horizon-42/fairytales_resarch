import React from "react";

export default function QASection({ qa, setQa }) {
  return (
    <section className="card">
      <h2>QA</h2>
      <div className="grid-3">
        <label>
          Annotator
          <input
            value={qa.annotator}
            onChange={(e) => setQa({ ...qa, annotator: e.target.value })}
          />
        </label>
        <label>
          Date annotated
          <input
            type="date"
            value={qa.date_annotated}
            onChange={(e) =>
              setQa({ ...qa, date_annotated: e.target.value })
            }
          />
        </label>
        <label>
          Confidence (0–1)
          <input
            type="number"
            step="0.01"
            min="0"
            max="1"
            value={qa.confidence}
            onChange={(e) =>
              setQa({ ...qa, confidence: Number(e.target.value) })
            }
          />
        </label>
      </div>

      <label>
        QA notes
        <textarea
          rows={2}
          value={qa.notes}
          onChange={(e) => setQa({ ...qa, notes: e.target.value })}
        />
      </label>
    </section>
  );
}

