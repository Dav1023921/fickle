import { Stage, Layer, Image } from 'react-konva';
import useImage from 'use-image';
import case257 from "./case257.jpg";
import Konva from "konva";
import { useRef } from "react";


// const stageRef = useRef<Konva.Stage | null>(null);

// const scaleImage = () => {
//     const stage = stageRef.current;


// }

type URLImageProps = {
  src: string;
  x?: number;
  y?: number;
};

const URLImage = ({ src, ...rest }: URLImageProps) => {
  const [image] = useImage(src, 'anonymous');
  return <Image image={image} draggable {...rest} />;
};

const Viewer = () => {
  return (
    <div style={{ border: "2px solid black", width: "600px", height: "600px" ,padding: "10px"}}>
        <Stage width={580} height={580}>
        <Layer>
            <URLImage src={case257} x={150} y={150} />
        </Layer>
        </Stage>
    </div>
  );
};

export default Viewer;