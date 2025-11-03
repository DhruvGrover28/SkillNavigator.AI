#!/bin/bash
# Render build script for SkillNavigator

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "📁 Creating frontend dist directory..."
mkdir -p backend/../frontend/dist

echo "📄 Creating placeholder index.html..."
cat > backend/../frontend/dist/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SkillNavigator - AI-Powered Job Application Platform</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
    <div class="min-h-screen flex items-center justify-center">
        <div class="max-w-md w-full space-y-8 p-8">
            <div class="text-center">
                <h1 class="text-3xl font-bold text-gray-900 mb-4">SkillNavigator</h1>
                <p class="text-gray-600 mb-8">AI-Powered Job Application Platform</p>
                <div class="bg-white p-6 rounded-lg shadow-md">
                    <h2 class="text-xl font-semibold mb-4">Login</h2>
                    <form class="space-y-4">
                        <input type="email" placeholder="Email" class="w-full p-3 border rounded-lg">
                        <input type="password" placeholder="Password" class="w-full p-3 border rounded-lg">
                        <button type="submit" class="w-full bg-blue-600 text-white p-3 rounded-lg hover:bg-blue-700">
                            Sign In
                        </button>
                    </form>
                    <p class="mt-4 text-sm text-gray-600">
                        Don't have an account? <a href="#" class="text-blue-600">Register</a>
                    </p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
EOF

echo "✅ Build complete!"