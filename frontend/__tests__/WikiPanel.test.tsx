import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import WikiPanel from "@/components/WikiPanel";

const mockSummary = {
  title: "Monstera deliciosa",
  description: "Species of flowering plant in the family Araceae",
  extract: "Monstera deliciosa, the Swiss cheese plant, is a species of flowering plant...",
  thumbnail: { source: "https://upload.wikimedia.org/monstera.jpg", width: 320, height: 427 },
  content_urls: { desktop: { page: "https://en.wikipedia.org/wiki/Monstera_deliciosa" } },
};

describe("WikiPanel", () => {
  it("renders title and description", () => {
    render(<WikiPanel summary={mockSummary} />);
    expect(screen.getByText("Monstera deliciosa")).toBeInTheDocument();
    expect(screen.getByText(/Species of flowering plant/)).toBeInTheDocument();
  });

  it("renders a link to Wikipedia", () => {
    render(<WikiPanel summary={mockSummary} />);
    const link = screen.getByRole("link", { name: /Full Wikipedia article/ });
    expect(link).toHaveAttribute("href", "https://en.wikipedia.org/wiki/Monstera_deliciosa");
  });

  it("renders a not-found message when summary is null", () => {
    render(<WikiPanel summary={null} />);
    expect(screen.getByText(/No Wikipedia article found/)).toBeInTheDocument();
  });
});
