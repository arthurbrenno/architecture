import ast
import os
from jinja2 import Environment, FileSystemLoader


def find_python_files(directory: str) -> list[str]:
    """Recursively finds all Python files in a directory."""
    python_files: list[str] = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def parse_file_for_markers(filepath: str) -> dict[str, set[str]]:
    """Parses a Python file to find classes and applied marker decorators."""
    with open(filepath, "r") as source:
        tree = ast.parse(source.read())

    file_marker_counts: dict[str, set[str]] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            applied_markers: set[str] = set()
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name):
                    applied_markers.add(decorator.id)
                elif isinstance(decorator, ast.Call) and isinstance(
                    decorator.func, ast.Name
                ):
                    applied_markers.add(
                        decorator.func.id
                    )  # Handle decorators with arguments if needed

            if applied_markers:
                file_marker_counts[class_name] = applied_markers

    return file_marker_counts


def generate_metrics_data(directory: str) -> dict[str, int]:
    """Generates the metrics data by scanning the codebase."""
    all_files = find_python_files(directory)
    marker_usage: dict[str, int] = {}

    for filepath in all_files:
        file_marker_data = parse_file_for_markers(filepath)
        for class_name, markers in file_marker_data.items():
            for marker in markers:
                marker_usage[marker] = marker_usage.get(marker, 0) + 1

    return marker_usage


def generate_html_report(metrics: dict[str, int]) -> str:
    """Generates an HTML report with a bar chart using Tailwind CSS and Chart.js."""
    env = Environment(loader=FileSystemLoader("."))
    template = env.from_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" integrity="sha512-9usAa10IRO0HhonpyAIVpjrylPvoDwiPUiKdWk5t3PyolY1cOd4DSE0Ga+ri4AuTroPR5aQvXU9xC6qOPnzFeg==" crossorigin="anonymous" referrerpolicy="no-referrer" />
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <title>Code Metrics Report</title>
    </head>
    <body class="bg-gradient-to-br from-gray-100 to-blue-50 dark:bg-gradient-to-br dark:from-gray-800 dark:to-gray-900">
        <div class="container mx-auto p-8 shadow-xl rounded-lg bg-white dark:bg-gray-800">
            <div class="text-center mb-8">
                <h1 class="text-4xl font-extrabold text-gray-800 dark:text-white mb-4">
                    <i class="fas fa-chart-line mr-2"></i> Interactive Code Metrics Dashboard
                </h1>
                <p class="text-gray-600 dark:text-gray-400 italic">Visualizing marker adoption across your codebase.</p>
            </div>
            <div class="mb-8">
                <canvas id="markerChart"></canvas>
            </div>
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700 shadow overflow-hidden rounded-md">
                    <thead class="bg-gray-50 dark:bg-gray-700">
                        <tr>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                <i class="fas fa-tags mr-1"></i> Marker
                            </th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                <i class="fas fa-sort-numeric-up-alt mr-1"></i> Count
                            </th>
                        </tr>
                    </thead>
                    <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                        {% for marker, count in metrics.items() %}
                        <tr>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100 font-medium">{{ marker }}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-400">{{ count }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        <script>
            const metrics = {{ metrics|tojson }};
            const ctx = document.getElementById('markerChart').getContext('2d');
            const markerChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: Object.keys(metrics),
                    datasets: [{
                        label: 'Marker Usage Count',
                        data: Object.values(metrics),
                        backgroundColor: 'rgba(54, 162, 235, 0.8)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Count'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Markers'
                            }
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: 'Marker Usage Distribution',
                            font: {
                                size: 18
                            }
                        },
                        legend: {
                            display: false,
                        }
                    }
                }
            });
        </script>
    </body>
    </html>
    """)
    return template.render(metrics=metrics)


def save_html_report(html_content: str, filepath: str) -> None:
    """Saves the HTML content to a file."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)


def generate_code_metrics(codebase_directory: str) -> str:
    """
    Generates code metrics and creates an HTML report, saving it to a file.
    """
    metrics_data = generate_metrics_data(codebase_directory)
    html_report = generate_html_report(metrics_data)
    report_filepath = "code_metrics_report.html"
    save_html_report(html_report, report_filepath)
    return report_filepath


def example() -> None:
    codebase_path = "my_codebase"  # Replace with the actual path to your codebase
    example_file_path = os.path.join(codebase_path, "example.py")

    if not os.path.exists(codebase_path):
        os.makedirs(codebase_path)
    with open(example_file_path, "w") as f:
        f.write("""
from markers import Factory, Singleton, Observer

@Factory
class MyFactory:
    pass

@Singleton
class MySingleton:
    pass

@Observer
class MyObserver:
    pass
        """)

    report_filepath = generate_code_metrics(codebase_path)
    full_report_path = os.path.abspath(report_filepath)
    print(f"Report saved to: {full_report_path}")
    print(f"Open the file '{report_filepath}' in your web browser to view the report.")

    # Delete the example.py file
    if os.path.exists(example_file_path):
        os.remove(example_file_path)
        print(f"Deleted temporary file: {example_file_path}")


if __name__ == "__main__":
    example()
