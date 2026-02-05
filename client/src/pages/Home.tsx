import { useGreeting } from "@/hooks/use-greeting";

export default function Home() {
  const { data, isLoading, error } = useGreeting();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error loading greeting.</div>;
  }

  return (
    <div>
      {data?.message || "Hello World"}
    </div>
  );
}
