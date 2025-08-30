import os
import json
import polars as pl

def create_3d_plot_html(csv_file_path, filename="3d_plot.html"):
    """
    Generates a self-contained HTML file for an interactive 3D scatter plot
    from data in a CSV file using Polars.

    Args:
        csv_file_path (str): The path to the CSV file containing the data.
        filename (str): The name of the HTML file to be created.
    """
    if not os.path.exists(csv_file_path):
        print(f"Error: The file '{csv_file_path}' does not exist.")
        return

    try:
        # Read the data from the CSV file using Polars
        df = pl.read_csv(csv_file_path)

        # Check for required columns
        required_cols = {'Wind Direction', 'Wind Speed', 'Temperature'}
        if not required_cols.issubset(df.columns):
            print(f"Error: The CSV file must contain 'Wind Direction', 'Wind Speed', and 'Temperature' columns. Found: {df.columns}")
            return

        # Convert Polars DataFrame to a list of dictionaries for JavaScript
        data_dicts = df.select(['Wind Direction', 'Wind Speed', 'Temperature']).to_dicts()
        data_json = json.dumps(data_dicts)

    except Exception as e:
        print(f"An error occurred while reading the CSV file: {e}")
        return

    # HTML content as a multi-line string with embedded data
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wind Data 3D Plot</title>
    <style>
        body {{
            margin: 0;
            overflow: hidden;
            font-family: sans-serif;
            background-color: #f0f0f0;
            color: #333;
        }}
        canvas {{
            display: block;
        }}
        .info {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(255, 255, 255, 0.7);
            padding: 10px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
        }}
        .container {{
            width: 100vw;
            height: 100vh;
        }}
    </style>
</head>
<body>
    <div class="info">
        <h1>Wind Data 3D Plot</h1>
        <p>X-axis: Wind Direction, Y-axis: Wind Speed, Z-axis: Temperature</p>
        <p>Use your mouse to rotate and zoom.</p>
    </div>
    <div class="container" id="plot-container"></div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>

    <script>
        // Data loaded from the CSV file
        const data = {data_json};

        // === Three.js Setup ===

        // Scene, camera, and renderer
        const container = document.getElementById('plot-container');
        let scene, camera, renderer, controls;
        let points = [];

        function init() {{
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0xf0f0f0);

            // Camera setup
            camera = new THREE.PerspectiveCamera(75, container.offsetWidth / container.offsetHeight, 0.1, 1000);
            camera.position.z = 30;

            // Renderer setup
            renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(container.offsetWidth, container.offsetHeight);
            container.appendChild(renderer.domElement);

            // Controls
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true; // For a smoother experience
            controls.dampingFactor = 0.05;
            controls.screenSpacePanning = false;
            controls.minDistance = 1;
            controls.maxDistance = 100;

            // Add coordinate axes
            const axesHelper = new THREE.AxesHelper(20);
            scene.add(axesHelper);

            // Add a light source
            const light = new THREE.AmbientLight(0x404040); // Soft white light
            scene.add(light);
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
            directionalLight.position.set(1, 1, 1);
            scene.add(directionalLight);

            // Create points from data
            const geometry = new THREE.SphereGeometry(0.5, 32, 32);
            const material = new THREE.MeshBasicMaterial({{ color: 0x0077ff }});

            data.forEach(pointData => {{
                const sphere = new THREE.Mesh(geometry, material);
                sphere.position.set(pointData['Wind Direction'], pointData['Wind Speed'], pointData['Temperature']);
                points.push(sphere);
                scene.add(sphere);
            }});

            // Handle window resizing
            window.addEventListener('resize', onWindowResize, false);
        }}

        function onWindowResize() {{
            camera.aspect = container.offsetWidth / container.offsetHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.offsetWidth, container.offsetHeight);
        }}

        // Animation loop
        function animate() {{
            requestAnimationFrame(animate);
            controls.update(); // Only required if controls.enableDamping is set to true
            renderer.render(scene, camera);
        }}

        // Initialize and start the animation loop
        init();
        animate();
    </script>
</body>
</html>
"""

    # Write the content to the specified file
    with open(filename, "w") as f:
        f.write(html_content)

    print(f"Successfully generated HTML file: {filename}")
    print(f"You can open it in your browser to view the interactive 3D plot.")

# Run the function to create the HTML file when the script is executed
if __name__ == "__main__":
    csv_file_path = "./src/data/nyc-tmy-2023.csv"
    create_3d_plot_html(csv_file_path)
