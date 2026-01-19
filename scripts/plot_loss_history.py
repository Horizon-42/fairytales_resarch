#!/usr/bin/env python3
"""Script to plot loss history from CSV files in models/loss_history directory."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Optional

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
except ImportError:
    print("Error: matplotlib is not installed. Install it with: pip install matplotlib")
    exit(1)


def load_loss_history(csv_file: Path) -> Dict[str, List]:
    """Load loss history from CSV file.
    
    Args:
        csv_file: Path to CSV file
        
    Returns:
        Dictionary with keys: steps, epochs, train_losses, eval_losses, learning_rates
    """
    data = {
        "steps": [],
        "epochs": [],
        "train_losses": [],
        "eval_losses": [],
        "learning_rates": [],
    }
    
    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    step = int(row.get("step", 0))
                    epoch = float(row.get("epoch", 0)) if row.get("epoch") else 0.0
                    train_loss = float(row.get("train_loss", "")) if row.get("train_loss") else None
                    eval_loss = float(row.get("eval_loss", "")) if row.get("eval_loss") else None
                    lr = float(row.get("learning_rate", "")) if row.get("learning_rate") else None
                    
                    data["steps"].append(step)
                    data["epochs"].append(epoch)
                    data["train_losses"].append(train_loss)
                    data["eval_losses"].append(eval_loss)
                    data["learning_rates"].append(lr)
                except (ValueError, KeyError) as e:
                    continue  # Skip invalid rows
    except Exception as e:
        print(f"Error reading {csv_file}: {e}")
        return None
    
    return data


def plot_loss_history(
    csv_files: List[Path],
    output_file: Optional[Path] = None,
    show_plot: bool = True,
    separate_plots: bool = False,
    train_only: bool = False,
):
    """Plot loss history from one or more CSV files.
    
    Args:
        csv_files: List of CSV file paths to plot
        output_file: Optional path to save the plot
        show_plot: Whether to display the plot
        separate_plots: If True, create separate subplots for each file
        train_only: If True, only plot train loss (skip eval loss)
    """
    if not csv_files:
        print("No CSV files provided")
        return
    
    # Load all data
    all_data = []
    for csv_file in csv_files:
        data = load_loss_history(csv_file)
        if data and data["steps"]:
            all_data.append((csv_file, data))
    
    if not all_data:
        print("No valid data found in CSV files")
        return
    
    # Create figure
    if separate_plots and len(all_data) > 1:
        fig, axes = plt.subplots(len(all_data), 1, figsize=(12, 6 * len(all_data)))
        if len(all_data) == 1:
            axes = [axes]
    else:
        fig, ax = plt.subplots(figsize=(12, 6))
        axes = [ax] * len(all_data)
    
    # Plot each file
    colors = plt.cm.tab10(range(len(all_data)))
    for idx, (csv_file, data) in enumerate(all_data):
        ax = axes[idx] if separate_plots else axes[0]
        
        # Extract step name from filename (e.g., "loss_history_character_20260119_030926.csv" -> "character")
        step_name = csv_file.stem.replace("loss_history_", "").split("_")[0]
        timestamp = "_".join(csv_file.stem.replace("loss_history_", "").split("_")[1:])
        label_prefix = f"{step_name}" if not separate_plots else f"{step_name} ({timestamp})"
        
        # Plot train loss - filter, remove duplicates, and sort by step
        train_data = {}
        for s, loss in zip(data["steps"], data["train_losses"]):
            if loss is not None:
                # If step already exists, keep the first one (or you could average them)
                if s not in train_data:
                    train_data[s] = loss
        
        if train_data:
            # Sort by step and convert to lists
            sorted_train = sorted(train_data.items())
            train_steps, train_losses = zip(*sorted_train)
            ax.plot(
                train_steps,
                train_losses,
                label=f"{label_prefix} - Train Loss",
                color=colors[idx],
                linestyle="-",
                linewidth=2,
                alpha=0.8,
                marker=".",
                markersize=3,
            )
        
        # Plot eval loss (only if train_only is False) - filter, remove duplicates, and sort by step
        if not train_only:
            eval_data = {}
            for s, loss in zip(data["steps"], data["eval_losses"]):
                if loss is not None:
                    # If step already exists, keep the first one (or you could average them)
                    if s not in eval_data:
                        eval_data[s] = loss
            
            if eval_data:
                # Sort by step and convert to lists
                sorted_eval = sorted(eval_data.items())
                eval_steps, eval_losses = zip(*sorted_eval)
                ax.plot(
                    eval_steps,
                    eval_losses,
                    label=f"{label_prefix} - Eval Loss",
                    color=colors[idx],
                    linestyle="--",
                    linewidth=2,
                    alpha=0.8,
                    marker="o",
                    markersize=4,
                )
        
        # Set labels and title
        ax.set_xlabel("Step", fontsize=12)
        ax.set_ylabel("Loss", fontsize=12)
        if separate_plots:
            title = f"Train Loss History: {step_name} ({timestamp})" if train_only else f"Loss History: {step_name} ({timestamp})"
            ax.set_title(title, fontsize=14, fontweight="bold")
        else:
            title = "Training Loss History" if train_only else "Training Loss History"
            ax.set_title(title, fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best", fontsize=10)
    
    plt.tight_layout()
    
    # Save plot if output file specified
    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        print(f"Plot saved to: {output_file}")
    
    # Show plot
    if show_plot:
        plt.show()
    else:
        plt.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Plot loss history from CSV files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Plot all loss history files
  python scripts/plot_loss_history.py

  # Plot specific files
  python scripts/plot_loss_history.py --files models/loss_history/loss_history_character_*.csv

  # Plot and save to file
  python scripts/plot_loss_history.py --output loss_plot.png

  # Create separate plots for each file
  python scripts/plot_loss_history.py --separate

  # Plot only train loss (skip eval loss)
  python scripts/plot_loss_history.py --train-only
        """
    )
    parser.add_argument(
        "--loss-history-dir",
        type=str,
        default="models/loss_history",
        help="Directory containing loss history CSV files (default: models/loss_history)"
    )
    parser.add_argument(
        "--files",
        type=str,
        nargs="+",
        default=None,
        help="Specific CSV files to plot (default: all files in loss_history_dir)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path to save the plot (e.g., loss_plot.png)"
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Don't display the plot (useful when only saving to file)"
    )
    parser.add_argument(
        "--separate",
        action="store_true",
        help="Create separate subplots for each file instead of overlaying"
    )
    parser.add_argument(
        "--step",
        type=str,
        nargs="+",
        default=None,
        help="Filter by step name(s) (e.g., --step character action)"
    )
    parser.add_argument(
        "--train-only",
        action="store_true",
        help="Only plot train loss, skip eval loss"
    )
    
    args = parser.parse_args()
    
    # Find CSV files
    loss_history_dir = Path(args.loss_history_dir)
    
    if args.files:
        # Use specified files
        csv_files = []
        for pattern in args.files:
            csv_files.extend(Path(".").glob(pattern))
        csv_files = sorted(set(csv_files))
    else:
        # Find all CSV files in directory
        if not loss_history_dir.exists():
            print(f"Error: Loss history directory not found: {loss_history_dir}")
            return 1
        csv_files = sorted(loss_history_dir.glob("loss_history_*.csv"))
    
    if not csv_files:
        print(f"No loss history CSV files found in {loss_history_dir}")
        return 1
    
    # Filter by step name if specified
    if args.step:
        filtered_files = []
        for csv_file in csv_files:
            step_name = csv_file.stem.replace("loss_history_", "").split("_")[0]
            if step_name in args.step:
                filtered_files.append(csv_file)
        csv_files = filtered_files
        
        if not csv_files:
            print(f"No files found for steps: {', '.join(args.step)}")
            return 1
    
    print(f"Found {len(csv_files)} loss history file(s):")
    for f in csv_files:
        print(f"  - {f}")
    
    # Plot
    output_path = Path(args.output) if args.output else None
    plot_loss_history(
        csv_files,
        output_file=output_path,
        show_plot=not args.no_show,
        separate_plots=args.separate,
        train_only=args.train_only,
    )
    
    return 0


if __name__ == "__main__":
    exit(main())
