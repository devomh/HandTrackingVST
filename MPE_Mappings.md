# Hand Movement to MIDI Control Mapping

| **Movement Type** | **Direction/Action** | **MIDI Control** | **CC Number** | **Range** | **Description** |
|-------------------|---------------------|------------------|---------------|-----------|-----------------|
| **Z-Axis** | Closer to camera | **Channel Pressure** | N/A (Channel Pressure) | 0-127 | Higher pressure values |
| **Z-Axis** | Further from camera | **Channel Pressure** | N/A (Channel Pressure) | 0-127 | Lower pressure values |
| **Z-Axis** (Fallback) | Depth variation | **Pressure CC** | **CC74** | 0-127 | When MPE disabled |
| **X-Axis** | Horizontal swipe right | **Pitch Bend** | N/A (Pitch Bend) | 0 to +8191 | Positive pitch bend |
| **X-Axis** | Horizontal swipe left | **Pitch Bend** | N/A (Pitch Bend) | 0 to -8192 | Negative pitch bend |
| **Y-Axis** | Vertical move up | **Expression** | **CC11** | 0-63 | Lower CC values |
| **Y-Axis** | Vertical move down | **Expression** | **CC11** | 65-127 | Higher CC values |
| **2D Speed** | Fast movement | **Note Velocity** | N/A (Velocity) | 1-127 | Higher velocity on note-on |
| **2D Speed** | Slow movement | **Note Velocity** | N/A (Velocity) | 1-127 | Lower velocity (min 64) |
| **2D Magnitude** | Overall movement | **Modulation** | **CC1** | 0-127 | Movement intensity |

## **Key Notes:**

- **Z-depth range**: `-0.1` (close) to `+0.1` (far) in MediaPipe coordinates
- **Pitch bend sensitivity**: Configurable via `pitch_bend_sensitivity` (default 2.0)
- **Center values**: Y-movement centers around CC11 = 64
- **Thresholds**: 
  - Velocity threshold: 0.01 units/frame
  - Pitch bend threshold: 0.05 slope units
- **MPE channels**: Each zone gets dedicated channel 2-16
- **Update rate**: ~30fps real-time expression updates

This mapping provides comprehensive 3D expression control optimized for musical performance!