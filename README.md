# Smart Mirror - Enhanced Virtual Try-On System

An AI-powered Smart Mirror with advanced virtual try-on capabilities using pose estimation, real-time background removal, and clothing-specific positioning algorithms.

## 🌟 Enhanced Features

### Core Improvements
- **Advanced Pose Estimation**: Enhanced MediaPipe Pose integration with confidence scoring and pose smoothing
- **Clothing-Specific Behavior**: Category-aware positioning for jackets, shirts, pants, dresses, and tank tops
- **Realistic Overlay Rendering**: Multi-layered shadow effects, anti-aliasing, and smooth scaling
- **Asynchronous Background Removal**: Non-blocking background processing with loading states
- **Intelligent Fallback System**: Automatic fallback when pose detection confidence is low
- **Performance Optimizations**: Smooth animations, hardware acceleration, and efficient rendering

### Virtual Try-On Capabilities

#### Clothing Categories with Specific Positioning:
- **Jackets**: Upper torso coverage with extended height and enhanced shadows
- **Shirts**: Standard torso fitting with balanced proportions
- **Tank Tops**: Shoulder-focused positioning with reduced width
- **Pants**: Hip-to-ankle alignment with extended leg coverage
- **Dresses**: Full-body coverage from shoulders to ankles

#### Enhanced Pose Detection:
- Real-time keypoint tracking with confidence scoring
- 5-frame pose history for smooth movement
- Automatic fallback when confidence drops below 60%
- Support for both MediaPipe naming conventions

#### Realistic Rendering:
- Category-specific shadow effects
- Multi-layer drop shadows for depth
- Anti-aliased image rendering
- Smooth scaling transitions
- Hardware-accelerated animations

## 🛠️ Technical Implementation

### Frontend Technologies
- **Pose Detection**: MediaPipe Pose with TensorFlow.js
- **Real-time Processing**: WebRTC for webcam access
- **Rendering**: CSS3 transforms with hardware acceleration
- **UI Framework**: Vanilla JavaScript with modern ES6+ features

### Backend Integration
- **Flask**: Python web framework
- **Background Removal**: rembg library with PIL
- **Caching**: Flask-Caching for performance
- **Real-time Communication**: Socket.IO

### Key Algorithms

#### 1. Pose Smoothing Algorithm
```javascript
// 5-frame moving average for stable tracking
function smoothPose(poseHistory) {
    // Weighted averaging across keypoints
    // Confidence-based filtering
    // Jitter reduction
}
```

#### 2. Clothing Category Detection
```javascript
// AI-powered category classification
function determineClothingCategory(item) {
    // Title and description analysis
    // Keyword matching
    // Category-specific configurations
}
```

#### 3. Dynamic Sizing Algorithm
```javascript
// Proportional scaling based on body measurements
function calculateClothingDimensions(keypoints, categoryConfig) {
    // Shoulder width calculation
    // Torso height measurement
    // Category-specific multipliers
}
```

## 🚀 Installation & Setup

### Prerequisites
```bash
Python 3.8+
Node.js (for package management)
Webcam access
Modern web browser with WebRTC support
```

### Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install rembg models (first run)
python -c "from rembg import new_session; new_session('u2net')"
```

### Frontend Dependencies
The system uses CDN-based loading for optimal performance:
- MediaPipe Pose
- TensorFlow.js
- Socket.IO
- Font Awesome

### Running the Application
```bash
python app.py
```
Access at `http://localhost:5000`

## 📋 API Endpoints

### Try-On System
- `GET /find_clothing` - Fetch clothing items with filters
- `POST /remove_background` - Async background removal
- `GET /` - Main interface

### Real-time Features
- `WebSocket: trigger_tryon` - Start try-on session
- `WebSocket: try_on_selected_item` - Select specific item

## 🎯 Usage Instructions

### Voice Commands
- "Show me jackets" - Display jacket options
- "Try on item 2" - Select specific clothing item
- Voice activation button for initial setup

### Manual Interaction
1. **Browse Options**: Clothing items display automatically
2. **Select Item**: Click on desired clothing piece
3. **Pose Detection**: Stand in front of camera for optimal tracking
4. **Automatic Fitting**: System adjusts clothing based on your pose

### Fallback Mode
When pose detection confidence is low:
- Automatic center positioning
- User notification message
- Graceful degradation

## 🔧 Configuration Options

### Pose Detection Settings
```javascript
const poseConfidenceThreshold = 0.6;  // Minimum confidence
const POSE_HISTORY_SIZE = 5;          // Smoothing window
```

### Clothing Categories
Modify `CLOTHING_CATEGORIES` object for custom clothing types:
```javascript
'custom-category': {
    name: 'custom',
    keypoints: ['leftShoulder', 'rightShoulder'],
    positioning: {
        widthMultiplier: 1.2,
        heightMultiplier: 1.5,
        topOffset: -0.1,
        centerOffset: { x: 0, y: 0 }
    },
    shadows: { blur: 6, spread: 2, opacity: 0.25 }
}
```

## 🎨 Styling Customization

### CSS Variables
Key styling can be modified through CSS custom properties:
- Shadow effects: Adjust blur, spread, and opacity
- Transition timing: Cubic-bezier curves for smooth animations
- Color schemes: Modify overlay and UI colors

### Performance CSS
- Hardware acceleration with `transform3d()`
- `will-change` properties for optimized rendering
- Backface visibility hidden for smooth animations

## 📱 Mobile Responsiveness

### Responsive Breakpoints
- Desktop: Full feature set
- Tablet: Optimized overlay sizing
- Mobile: Compact UI with essential features

### Touch Interactions
- Touch-friendly product cards
- Swipe gestures for browsing
- Optimized loading indicators

## 🔍 Troubleshooting

### Common Issues

**Pose Detection Not Working**
- Check webcam permissions
- Ensure good lighting
- Verify MediaPipe model loading

**Background Removal Slow**
- Check server performance
- Verify rembg installation
- Consider model optimization

**Overlay Positioning Issues**
- Calibrate pose confidence threshold
- Check keypoint visibility
- Verify clothing category detection

### Performance Optimization

**Frontend**
- Enable hardware acceleration
- Use requestAnimationFrame for smooth animations
- Implement efficient DOM updates

**Backend**
- Cache processed images
- Optimize rembg model loading
- Use async processing

## 🛡️ Browser Compatibility

### Supported Browsers
- Chrome 80+ (Recommended)
- Firefox 75+
- Safari 13+
- Edge 80+

### Required Features
- WebRTC camera access
- ES6+ JavaScript support
- CSS3 transforms and filters
- Canvas and WebGL support

## 📊 Performance Metrics

### Target Performance
- Pose detection: 30 FPS
- Background removal: <3 seconds
- Overlay rendering: 60 FPS
- Memory usage: <500MB

### Optimization Features
- Lazy loading for product images
- Efficient pose smoothing algorithms
- Hardware-accelerated CSS animations
- Optimized WebGL usage

## 🔮 Future Enhancements

### Planned Features
- 3D clothing models
- Size recommendation AI
- Multiple clothing items simultaneously
- Augmented reality integration
- Social sharing capabilities

### Technical Roadmap
- WebAssembly for faster processing
- Machine learning model optimization
- Enhanced pose estimation models
- Real-time lighting adjustments

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Implement enhancements
4. Add comprehensive tests
5. Submit pull request

## 📞 Support

For technical support or feature requests:
- Open GitHub issue
- Check troubleshooting guide
- Review API documentation 