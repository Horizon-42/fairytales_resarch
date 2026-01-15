"""Visualization module for text segmentation debugging and validation.

This module provides non-intrusive visualization tools for:
- Similarity matrix heatmaps
- Magnetic Clustering signal analysis
- GraphSegSM graph structure
- Segmentation comparison barcodes
"""

from __future__ import annotations

from typing import List, Optional

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import seaborn as sns


class SegmentationVisualizer:
    """Non-intrusive visualizer for text segmentation algorithms.
    
    This class provides visualization methods that work with existing
    segmentation results without modifying the core algorithms.
    """

    def __init__(self, figsize: tuple = (12, 8)):
        """Initialize the visualizer.
        
        Args:
            figsize: Default figure size for plots.
        """
        self.figsize = figsize
        sns.set_style("whitegrid")

    def plot_similarity_matrix(
        self,
        similarity_matrix: np.ndarray,
        ground_truth_boundaries: Optional[List[int]] = None,
        title: str = "Cosine Similarity Matrix",
        save_path: Optional[str] = None,
    ) -> None:
        """Plot similarity matrix heatmap with optional boundary overlays.
        
        Args:
            similarity_matrix: Similarity matrix of shape (n, n).
            ground_truth_boundaries: Optional list of ground truth boundary indices.
            title: Plot title.
            save_path: Optional path to save the figure.
        """
        plt.figure(figsize=self.figsize)
        
        # Draw heatmap
        sns.heatmap(
            similarity_matrix,
            cmap="magma",
            square=True,
            cbar_kws={'label': 'Similarity'},
            xticklabels=False,
            yticklabels=False,
        )
        
        # Overlay ground truth boundaries if provided
        if ground_truth_boundaries:
            for boundary in ground_truth_boundaries:
                # Draw horizontal and vertical lines at boundary positions
                plt.axhline(
                    boundary,
                    color='cyan',
                    linestyle='--',
                    linewidth=1,
                    alpha=0.7,
                    label='Ground Truth' if boundary == ground_truth_boundaries[0] else "",
                )
                plt.axvline(
                    boundary,
                    color='cyan',
                    linestyle='--',
                    linewidth=1,
                    alpha=0.7,
                )
            
            if ground_truth_boundaries:
                plt.legend()
        
        plt.title(title)
        plt.xlabel("Sentence Index")
        plt.ylabel("Sentence Index")
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()

    def plot_magnetic_signal(
        self,
        b_values: np.ndarray,
        smoothed_b_values: Optional[np.ndarray] = None,
        predicted_boundaries: Optional[List[int]] = None,
        title: str = "Magnetic Clustering Signal Analysis",
        save_path: Optional[str] = None,
    ) -> None:
        """Plot magnetic force signal with smoothing and boundary predictions.
        
        Args:
            b_values: Raw magnetic force values, shape (n-1,).
            smoothed_b_values: Optional smoothed signal values.
            predicted_boundaries: Optional list of predicted boundary indices.
            title: Plot title.
            save_path: Optional path to save the figure.
        """
        x = np.arange(len(b_values))
        
        plt.figure(figsize=(12, 4))
        
        # 1. Plot raw magnetic values
        plt.plot(
            x,
            b_values,
            label='Raw Magnetization ($b_i$)',
            color='lightgray',
            alpha=0.5,
            linewidth=1,
        )
        
        # 2. Plot smoothed values if provided
        if smoothed_b_values is not None:
            plt.plot(
                x,
                smoothed_b_values,
                label='Smoothed Signal',
                color='purple',
                linewidth=2,
            )
            target_signal = smoothed_b_values
        else:
            target_signal = b_values
        
        # 3. Draw zero line
        plt.axhline(0, color='black', linestyle='-', linewidth=1, alpha=0.5)
        
        # 4. Mark predicted boundaries
        if predicted_boundaries:
            for idx in predicted_boundaries:
                if 0 <= idx < len(b_values):
                    plt.axvline(
                        x=idx,
                        color='red',
                        linestyle='--',
                        linewidth=2,
                        alpha=0.7,
                        label='Predicted Boundary' if idx == predicted_boundaries[0] else "",
                    )
        
        # 5. Fill areas above and below zero
        plt.fill_between(
            x,
            target_signal,
            0,
            where=(target_signal > 0),
            color='blue',
            alpha=0.1,
            interpolate=True,
        )
        plt.fill_between(
            x,
            target_signal,
            0,
            where=(target_signal < 0),
            color='red',
            alpha=0.1,
            interpolate=True,
        )
        
        plt.title(title)
        plt.xlabel("Sentence Gap Index")
        plt.ylabel("Magnetization Strength ($b_i$)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()

    def plot_graph_structure(
        self,
        similarity_matrix: np.ndarray,
        threshold: float,
        segment_window: tuple[int, int] = (0, 50),
        title: Optional[str] = None,
        save_path: Optional[str] = None,
    ) -> None:
        """Plot graph structure visualization with adjacency matrix and network graph.
        
        Args:
            similarity_matrix: Similarity matrix of shape (n, n).
            threshold: Similarity threshold for edge creation.
            segment_window: Tuple of (start, end) indices for the segment to visualize.
            title: Optional title for the plot.
            save_path: Optional path to save the figure.
        """
        # 1. Create binary adjacency matrix
        adj_matrix = (similarity_matrix > threshold).astype(int)
        
        start, end = segment_window
        end = min(end, similarity_matrix.shape[0])
        subset_adj = adj_matrix[start:end, start:end]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # 2. Plot adjacency matrix heatmap
        sns.heatmap(
            subset_adj,
            ax=ax1,
            cbar=False,
            cmap="Greys",
            square=True,
            xticklabels=False,
            yticklabels=False,
        )
        ax1.set_title(f"Thresholded Adjacency Matrix (τ={threshold:.2f})")
        ax1.set_xlabel(f"Sentence Index ({start}-{end})")
        ax1.set_ylabel(f"Sentence Index ({start}-{end})")
        
        # 3. Build and visualize network graph
        G = nx.Graph()
        rows, cols = np.where(subset_adj == 1)
        for r, c in zip(rows, cols):
            if r != c:  # Ignore self-loops
                G.add_edge(r + start, c + start)
        
        if len(G.nodes()) > 0:
            # Find cliques for coloring
            cliques = list(nx.find_cliques(G))
            
            # Color nodes by clique membership
            node_colors = []
            node_to_clique = {}
            for i, clique in enumerate(cliques):
                for node in clique:
                    if node not in node_to_clique or len(clique) > len(node_to_clique[node]):
                        node_to_clique[node] = clique
            
            color_map = {}
            for i, clique in enumerate(cliques):
                for node in clique:
                    color_map[node] = i
            
            node_colors = [color_map.get(node, -1) for node in G.nodes()]
            
            # Layout and draw
            try:
                pos = nx.spring_layout(G, seed=42, k=0.5, iterations=50)
            except Exception:
                pos = nx.spring_layout(G, seed=42)
            
            nx.draw(
                G,
                pos,
                ax=ax2,
                with_labels=True,
                node_color=node_colors if node_colors else None,
                cmap="tab20" if node_colors else None,
                node_size=300,
                font_size=8,
                edge_color='gray',
                alpha=0.7,
            )
            ax2.set_title(f"Semantic Graph (Sentences {start}-{end})")
        else:
            ax2.text(0.5, 0.5, "No edges in this segment", ha='center', va='center')
            ax2.set_title(f"Semantic Graph (Sentences {start}-{end})")
        
        if title:
            fig.suptitle(title, fontsize=14)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()

    def plot_segmentation_comparison(
        self,
        doc_len: int,
        true_boundaries: List[int],
        pred_boundaries: List[int],
        metric_score: Optional[float] = None,
        tolerance: int = 2,
        title: str = "Segmentation Comparison",
        save_path: Optional[str] = None,
    ) -> None:
        """Plot segmentation comparison barcode showing predicted vs ground truth boundaries.
        
        Args:
            doc_len: Total number of sentences in the document.
            true_boundaries: List of ground truth boundary indices.
            pred_boundaries: List of predicted boundary indices.
            metric_score: Optional boundary similarity score to display.
            tolerance: Tolerance for near-miss detection (for coloring).
            title: Plot title.
            save_path: Optional path to save the figure.
        """
        fig, ax = plt.subplots(figsize=(max(12, doc_len / 10), 3))
        
        # Set up axes
        ax.set_ylim(0, 2)
        ax.set_xlim(-0.5, doc_len - 0.5)
        ax.set_yticks([0.5, 1.5])
        ax.set_yticklabels(["Prediction", "Ground Truth"])
        ax.set_xlabel("Sentence Index")
        
        # Draw Ground Truth boundaries
        for b in true_boundaries:
            if 0 <= b < doc_len:
                ax.vlines(
                    b,
                    1,
                    2,
                    colors='green',
                    linewidth=3,
                    alpha=0.8,
                    label='Ground Truth' if b == true_boundaries[0] else "",
                )
        
        # Draw Prediction boundaries with color coding
        true_set = set(true_boundaries)
        near_miss_set = set()
        
        # Identify near misses
        for pred_b in pred_boundaries:
            if pred_b not in true_set:
                for true_b in true_boundaries:
                    if abs(pred_b - true_b) < tolerance:
                        near_miss_set.add(pred_b)
                        break
        
        for b in pred_boundaries:
            if 0 <= b < doc_len:
                if b in true_set:
                    color = 'green'  # Exact match
                    label = 'Match' if b == pred_boundaries[0] or (b == pred_boundaries[0] and b not in true_set) else ""
                elif b in near_miss_set:
                    color = 'orange'  # Near miss
                    label = 'Near Miss' if b == pred_boundaries[0] or (b == pred_boundaries[0] and b not in true_set) else ""
                else:
                    color = 'red'  # False positive
                    label = 'False Positive' if b == pred_boundaries[0] or (b == pred_boundaries[0] and b not in true_set) else ""
                
                ax.vlines(
                    b,
                    0,
                    1,
                    colors=color,
                    linewidth=3,
                    alpha=0.8,
                    label=label if label else "",
                )
        
        # Add grid for easier reading
        ax.grid(True, axis='x', which='both', linestyle='--', alpha=0.3)
        ax.set_axisbelow(True)
        
        # Build title
        plot_title = title
        if metric_score is not None:
            plot_title += f" (Boundary Score: {metric_score:.4f})"
        plt.title(plot_title)
        
        # Add legend
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        if by_label:
            ax.legend(by_label.values(), by_label.keys(), loc='upper right')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()


def visualize_segmentation_result(
    result,
    similarity_matrix: Optional[np.ndarray] = None,
    reference_boundaries: Optional[List[int]] = None,
    magnetic_data: Optional[dict] = None,
    visualizer: Optional[SegmentationVisualizer] = None,
    save_dir: Optional[str] = None,
) -> None:
    """Convenience function to visualize a complete segmentation result.
    
    This function provides a non-intrusive way to visualize segmentation
    results by accepting optional intermediate data.
    
    Args:
        result: SegmentationResult object from TextSegmenter.segment().
        similarity_matrix: Optional similarity matrix for visualization.
        reference_boundaries: Optional reference boundaries for comparison.
        magnetic_data: Optional dict with 'raw_forces' and 'smoothed_forces'
            for Magnetic Clustering visualization.
        visualizer: Optional SegmentationVisualizer instance. If None, creates a new one.
        save_dir: Optional directory to save figures.
    """
    if visualizer is None:
        visualizer = SegmentationVisualizer()
    
    import os
    
    # 1. Plot similarity matrix if available
    if similarity_matrix is not None:
        save_path = os.path.join(save_dir, "similarity_matrix.png") if save_dir else None
        visualizer.plot_similarity_matrix(
            similarity_matrix,
            ground_truth_boundaries=reference_boundaries,
            title=f"Similarity Matrix - {result.document_id}",
            save_path=save_path,
        )
    
    # 2. Plot magnetic signal if available
    if magnetic_data is not None and result.meta.get("algorithm") == "magnetic":
        raw_forces = magnetic_data.get("raw_forces")
        smoothed_forces = magnetic_data.get("smoothed_forces")
        if raw_forces is not None:
            save_path = os.path.join(save_dir, "magnetic_signal.png") if save_dir else None
            visualizer.plot_magnetic_signal(
                raw_forces,
                smoothed_forces,
                predicted_boundaries=result.boundaries,
                title=f"Magnetic Signal - {result.document_id}",
                save_path=save_path,
            )
    
    # 3. Plot segmentation comparison if reference boundaries available
    if reference_boundaries is not None:
        # Calculate document length from segments
        doc_len = 0
        if result.segments:
            doc_len = result.segments[-1]["end_sentence_idx"] + 1
        
        if doc_len > 0:
            save_path = os.path.join(save_dir, "segmentation_comparison.png") if save_dir else None
            visualizer.plot_segmentation_comparison(
                doc_len=doc_len,
                true_boundaries=reference_boundaries,
                pred_boundaries=result.boundaries,
                metric_score=result.meta.get("evaluation_score"),
                title=f"Segmentation Comparison - {result.document_id}",
                save_path=save_path,
            )
