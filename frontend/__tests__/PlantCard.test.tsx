import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import PlantCard from "@/components/PlantCard";

const mockPrediction = {
  species: "Monstera deliciosa",
  common_name: "Swiss Cheese Plant",
  confidence: 0.91,
};

describe("PlantCard", () => {
  it("renders species and common name", () => {
    render(<PlantCard prediction={mockPrediction} rank={0} />);
    expect(screen.getByText("Swiss Cheese Plant")).toBeInTheDocument();
    expect(screen.getByText("Monstera deliciosa")).toBeInTheDocument();
  });

  it("displays confidence percentage", () => {
    render(<PlantCard prediction={mockPrediction} rank={0} />);
    expect(screen.getByText("91%")).toBeInTheDocument();
  });

  it("applies primary styling for rank 0", () => {
    const { container } = render(<PlantCard prediction={mockPrediction} rank={0} />);
    expect(container.firstChild).toHaveClass("border-garden-400");
  });

  it("applies secondary styling for rank > 0", () => {
    const { container } = render(<PlantCard prediction={mockPrediction} rank={1} />);
    expect(container.firstChild).toHaveClass("border-gray-200");
  });
});
