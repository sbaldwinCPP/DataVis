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
        # Read the data from the CSV file using Polars, skipping the first 2 rows
        df = pl.read_csv(csv_file_path, skip_rows=2)

        # Check for required columns
        required_cols = {'Wind Direction', 'Wind Speed', 'Temperature'}
        if not required_cols.issubset(df.columns):
            print(f"Error: The CSV file must contain 'Wind Direction', 'Wind Speed', and 'Temperature' columns. Found: {df.columns}")
            return

        # Convert Polars DataFrame to a list of dictionaries for JavaScript
        data_dicts = df.select(['Wind Direction', 'Wind Speed', 'Temperature']).to_dicts()

        # Find min/max values for scaling and labeling
        min_max_values = {
            "Wind Direction": {"min": df['Wind Direction'].min(), "max": df['Wind Direction'].max()},
            "Wind Speed": {"min": df['Wind Speed'].min(), "max": df['Wind Speed'].max()},
            "Temperature": {"min": df['Temperature'].min(), "max": df['Temperature'].max()}
        }
        
        # Combine data and ranges into a single JSON object
        plot_data = {
            "points": data_dicts,
            "ranges": min_max_values
        }

        data_json = json.dumps(plot_data, indent=4)

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
            font-size: 14px;
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
        <p>Use your mouse to rotate and zoom. Point colors are based on temperature (blue = cold, red = hot).</p>
    </div>
    <div class="container" id="plot-container"></div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>

    <script>
        // Data loaded from the CSV file
        const plotData = {data_json};
        const data = plotData.points;
        const ranges = plotData.ranges;
        const AXIS_LENGTH = 30;
        const AXIS_EXTENT = AXIS_LENGTH / 2;

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
            camera.position.set(AXIS_EXTENT * 1.5, AXIS_EXTENT * 1.5, AXIS_EXTENT * 1.5);
            camera.lookAt(0, 0, 0);

            // Renderer setup
            renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(container.offsetWidth, container.offsetHeight);
            container.appendChild(renderer.domElement);

            // Controls
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true; 
            controls.dampingFactor = 0.05;
            controls.screenSpacePanning = false;
            controls.minDistance = 1;
            controls.maxDistance = 200;

            // Add light sources
            const ambientLight = new THREE.AmbientLight(0x404040); 
            scene.add(ambientLight);
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
            directionalLight.position.set(1, 1, 1);
            scene.add(directionalLight);
            
            // Add a bounding box for a cleaner visual
            const boundingBox = new THREE.Box3(
                new THREE.Vector3(-AXIS_EXTENT, -AXIS_EXTENT, -AXIS_EXTENT),
                new THREE.Vector3(AXIS_EXTENT, AXIS_EXTENT, AXIS_EXTENT)
            );
            const boxHelper = new THREE.Box3Helper(boundingBox, 0x888888);
            scene.add(boxHelper);

            // Create points from data
            const geometry = new THREE.SphereGeometry(0.5, 32, 32);

            // Find min/max temperature for color scaling
            let minTemp = ranges['Temperature'].min;
            let maxTemp = ranges['Temperature'].max;

            // Define the color scale
            const startColor = new THREE.Color(0x0000ff); // Blue for cold
            const endColor = new THREE.Color(0xff0000); // Red for hot

            data.forEach(pointData => {{
                // Normalize temperature to a 0-1 range
                const normalizedTemp = (pointData.Temperature - minTemp) / (maxTemp - minTemp);
                // Interpolate color based on normalized temperature
                const pointColor = startColor.clone().lerp(endColor, normalizedTemp);
                
                const material = new THREE.MeshBasicMaterial({{ color: pointColor }});
                const sphere = new THREE.Mesh(geometry, material);

                // Scale data to fit within the centered range
                const x = THREE.MathUtils.mapLinear(pointData['Wind Direction'], ranges['Wind Direction'].min, ranges['Wind Direction'].max, -AXIS_EXTENT, AXIS_EXTENT);
                const y = THREE.MathUtils.mapLinear(pointData['Wind Speed'], ranges['Wind Speed'].min, ranges['Wind Speed'].max, -AXIS_EXTENT, AXIS_EXTENT);
                const z = THREE.MathUtils.mapLinear(pointData['Temperature'], ranges['Temperature'].min, ranges['Temperature'].max, -AXIS_EXTENT, AXIS_EXTENT);
                
                sphere.position.set(x, y, z);
                points.push(sphere);
                scene.add(sphere);
            }});

            // Add axes and labels
            createAxesAndLabels();
            
            // Handle window resizing
            window.addEventListener('resize', onWindowResize, false);
        }}
        
        function createTextCanvas(text) {{
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            const fontSize = 100;
            context.font = `${{fontSize}}px Arial`;
            const textMetrics = context.measureText(text);
            const textWidth = textMetrics.width;
            const textHeight = fontSize;
            canvas.width = textWidth;
            canvas.height = textHeight;
            context.font = `${{fontSize}}px Arial`;
            context.fillStyle = 'black';
            context.fillText(text, 0, fontSize);
            return canvas;
        }}

        function createLabel(text, position) {{
            const canvas = createTextCanvas(text);
            const texture = new THREE.CanvasTexture(canvas);
            const material = new THREE.SpriteMaterial({{ map: texture }});
            const sprite = new THREE.Sprite(material);
            sprite.scale.set(canvas.width / 50, canvas.height / 50, 1);
            sprite.position.copy(position);
            scene.add(sprite);
            return sprite;
        }}

        function createAxesAndLabels() {{
            const tickCount = 5;
            const xStep = (ranges['Wind Direction'].max - ranges['Wind Direction'].min) / (tickCount - 1);
            const yStep = (ranges['Wind Speed'].max - ranges['Wind Speed'].min) / (tickCount - 1);
            const zStep = (ranges['Temperature'].max - ranges['Temperature'].min) / (tickCount - 1);
            
            // Draw axis lines and labels on the plot boundary
            
            // X-Axis (Wind Direction)
            const xMaterial = new THREE.LineBasicMaterial({{ color: 0xff0000 }});
            const xGeometry = new THREE.BufferGeometry().setFromPoints([
                new THREE.Vector3(-AXIS_EXTENT, -AXIS_EXTENT, -AXIS_EXTENT), 
                new THREE.Vector3(AXIS_EXTENT, -AXIS_EXTENT, -AXIS_EXTENT)
            ]);
            const xAxis = new THREE.Line(xGeometry, xMaterial);
            scene.add(xAxis);
            createLabel("Wind Direction", new THREE.Vector3(AXIS_EXTENT + 5, -AXIS_EXTENT, -AXIS_EXTENT));

            // Y-Axis (Wind Speed)
            const yMaterial = new THREE.LineBasicMaterial({{ color: 0x00ff00 }});
            const yGeometry = new THREE.BufferGeometry().setFromPoints([
                new THREE.Vector3(-AXIS_EXTENT, -AXIS_EXTENT, -AXIS_EXTENT), 
                new THREE.Vector3(-AXIS_EXTENT, AXIS_EXTENT, -AXIS_EXTENT)
            ]);
            const yAxis = new THREE.Line(yGeometry, yMaterial);
            scene.add(yAxis);
            createLabel("Wind Speed", new THREE.Vector3(-AXIS_EXTENT, AXIS_EXTENT + 5, -AXIS_EXTENT));

            // Z-Axis (Temperature)
            const zMaterial = new THREE.LineBasicMaterial({{ color: 0x0000ff }});
            const zGeometry = new THREE.BufferGeometry().setFromPoints([
                new THREE.Vector3(-AXIS_EXTENT, -AXIS_EXTENT, -AXIS_EXTENT), 
                new THREE.Vector3(-AXIS_EXTENT, -AXIS_EXTENT, AXIS_EXTENT)
            ]);
            const zAxis = new THREE.Line(zGeometry, zMaterial);
            scene.add(zAxis);
            createLabel("Temperature", new THREE.Vector3(-AXIS_EXTENT, -AXIS_EXTENT, AXIS_EXTENT + 5));

            // Add tick marks and values
            for (let i = 0; i < tickCount; i++) {{
                // X-axis ticks
                const xVal = ranges['Wind Direction'].min + i * xStep;
                const xPos = THREE.MathUtils.mapLinear(xVal, ranges['Wind Direction'].min, ranges['Wind Direction'].max, -AXIS_EXTENT, AXIS_EXTENT);
                createLabel(xVal.toFixed(0), new THREE.Vector3(xPos, -AXIS_EXTENT - 2, -AXIS_EXTENT));

                // Y-axis ticks
                const yVal = ranges['Wind Speed'].min + i * yStep;
                const yPos = THREE.MathUtils.mapLinear(yVal, ranges['Wind Speed'].min, ranges['Wind Speed'].max, -AXIS_EXTENT, AXIS_EXTENT);
                createLabel(yVal.toFixed(1), new THREE.Vector3(-AXIS_EXTENT - 2, yPos, -AXIS_EXTENT));

                // Z-axis ticks
                const zVal = ranges['Temperature'].min + i * zStep;
                const zPos = THREE.MathUtils.mapLinear(zVal, ranges['Temperature'].min, ranges['Temperature'].max, -AXIS_EXTENT, AXIS_EXTENT);
                createLabel(zVal.toFixed(1), new THREE.Vector3(-AXIS_EXTENT - 2, -AXIS_EXTENT, zPos));
            }}
        }}

        function onWindowResize() {{
            camera.aspect = container.offsetWidth / container.offsetHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.offsetWidth, container.offsetHeight);
        }}

        // Animation loop
        function animate() {{
            requestAnimationFrame(animate);
            controls.update(); 
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
