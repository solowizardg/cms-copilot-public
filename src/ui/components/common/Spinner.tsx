import { React } from "../../hooks";

export const Spinner: React.FC = () => {
    return (
        <span
            className="lgui-spin"
            style={{
                display: "inline-block",
                width: 14,
                height: 14,
                borderRadius: "50%",
                border: "2px solid #e2e8f0",
                borderTopColor: "#3b82f6",
            }}
        />
    );
};
