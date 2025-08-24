import axios from "axios"

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000"

export const injestDocuments = async (data, isFile = false) => {
  const url = `${BASE_URL}/retriever/ingest`
  try {
    const resp = await axios.post(url, data, {
      headers: isFile ? undefined : { "Content-Type": "application/json" },
      withCredentials: false, 
    })
    return resp.data
  } catch (err) {
    throw err
  }
}

export const experimentResults = async (task_id) => {
  const url = `${BASE_URL}/experiment/result/${task_id}`
  try {
    const resp = await axios.post(url)
    return resp.data
  } catch (err) {
    throw err
  }
}
