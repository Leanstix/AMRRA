"use client"
import { ExperimentResultPage } from "@/components/experimentation/ExperimentResultPage"
import { useState, useEffect } from "react"
import { experimentResults } from "@/lib/api"

const Page = ({ params }) => {
  const [result, setResult] = useState(null);

  useEffect(() => {
    const fetchResult = async () => {
      const data = await experimentResults(params.id);
      setResult(data);
    };

    fetchResult();
  }, [params.id]);

  if (!result) {
    return <div>Loading...</div>;
  }

  return <ExperimentResultPage result={result} />;
};

export default Page;
