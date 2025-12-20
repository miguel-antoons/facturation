import { HexColorPicker } from "react-colorful";
import "@/styles/swatchesPicker.css";

const SwatchesPicker = ({
  color,
  onChange,
  presetColors,
}: {
  color: string;
  onChange: (newVal: string) => void;
  presetColors: string[];
}) => {
  return (
    <div className="picker">
      <HexColorPicker color={color} onChange={onChange} />

      <div className="picker__swatches">
        {presetColors.map((presetColor: string) => (
          <button
            key={presetColor}
            className="picker__swatch"
            style={{ background: presetColor }}
            onClick={() => onChange(presetColor)}
          />
        ))}
      </div>
    </div>
  );
};

export default SwatchesPicker;
