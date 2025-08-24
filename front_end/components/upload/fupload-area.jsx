"use client"

import { useState, useCallback } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Upload, FileText, X } from "lucide-react"
import { Input } from "@/components/ui/input"
import { useToast } from "@/components/ui/use-toast"
import { Separator } from "@/components/ui/separator"
import { injestDocuments } from "@/lib/api"

export function UploadArea() {
  const [isDragOver, setIsDragOver] = useState(false)
  const [uploadedFile, setUploadedFile] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [paperUrl, setPaperUrl] = useState("")
  const [isFetching, setIsFetching] = useState(false)
  const { toast } = useToast()

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setIsDragOver(false)

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      const file = files[0]
      if (file.type === "application/pdf" || file.name.endsWith(".pdf")) {
        setUploadedFile(file)
      }
    }
  }, [])

  const handleFileSelect = useCallback((e) => {
    const files = e.target.files
    if (files && files.length > 0) {
      const file = files[0]
      setUploadedFile(file)
    }
  }, [])

  const handleRemoveFile = useCallback(() => {
    setUploadedFile(null)
  }, [])

  const handleProcessPaper = useCallback(async () => {
    if (!uploadedFile) return
    setIsProcessing(true)

    try {
      const formData = new FormData()
      formData.append("files", uploadedFile)
      formData.append(
        "request",
        JSON.stringify({
          items: [{ doc_id: uploadedFile.name, title: uploadedFile.name }]
        })
      )

      await injestDocuments(formData, true) 

      toast({ title: "Success", description: "Paper processed successfully!" })
      setTimeout(() => {
        setIsProcessing(false)
        window.location.href = "/hypotheses"
      }, 800)
    } catch (error) {
      setIsProcessing(false)
      const detail =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        error?.message ||
        "Could not process the uploaded file"
      toast({ title: "Error", description: detail, variant: "destructive" })
    }
  }, [uploadedFile, toast])

  const handleFetchPaper = useCallback(async () => {
    const raw = paperUrl.trim()
    if (!raw) {
      toast({
        title: "Error",
        description: "Please enter a valid paper URL",
        variant: "destructive"
      })
      return
    }

    const normalizedUrl = /^https?:\/\//i.test(raw) ? raw : `https://${raw}`

    setIsFetching(true)
    try {
      await injestDocuments({
        items: [
          {
            doc_id: "url_" + Date.now(),
            title: "Fetched Paper",
            url: normalizedUrl
          }
        ]
      })

      toast({ title: "Success", description: "Paper fetched successfully!" })
      setIsFetching(false)
      setIsProcessing(true)
      setTimeout(() => {
        setIsProcessing(false)
        window.location.href = "/hypotheses"
      }, 800)
    } catch (error) {
      setIsFetching(false)
      const detail =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        error?.message ||
        "Could not fetch this paper"
      toast({ title: "Error", description: detail, variant: "destructive" })
    }
  }, [paperUrl, toast])

  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  return (
    <Card className="p-8">
      <div className="space-y-6">
        <h2 className="text-2xl font-semibold text-foreground academic-text">Upload Research Paper</h2>

        {!uploadedFile ? (
          <>
            <div
              className={`
                border-2 border-dashed rounded-lg p-12 text-center transition-colors
                ${isDragOver ? "border-primary bg-accent/20" : "border-border hover:border-primary/50"}
              `}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <Upload className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-lg text-foreground academic-text mb-2">Drag and drop your ML paper here</p>
              <p className="text-muted-foreground control-text mb-4">or click to browse files</p>
              <input type="file" accept=".pdf" onChange={handleFileSelect} className="hidden" id="file-upload" />
              <Button asChild variant="outline" className="control-text bg-transparent">
                <label htmlFor="file-upload" className="cursor-pointer">
                  Choose File
                </label>
              </Button>
              <p className="text-sm text-muted-foreground control-text mt-2">Supports PDF files up to 10MB</p>
            </div>

            <div className="text-center">
              <div className="flex items-center gap-2 my-4">
                <Separator className="flex-1" />
                <span className="text-sm text-muted-foreground">OR</span>
                <Separator className="flex-1" />
              </div>

              <div className="flex flex-col sm:flex-row gap-2">
                <div className="flex-1">
                  <Input
                    type="text"
                    placeholder="https://arxiv.org/abs/1234.5678"
                    value={paperUrl}
                    onChange={(e) => setPaperUrl(e.target.value)}
                    className="w-full"
                    disabled={isFetching}
                  />
                </div>
                <Button
                  onClick={handleFetchPaper}
                  disabled={isFetching || isProcessing}
                  className="control-text"
                >
                  {isFetching ? "Fetching..." : "Fetch Paper"}
                </Button>
              </div>
            </div>
          </>
        ) : (
          <div className="space-y-4">
            <Card className="p-4 bg-accent/10 border-accent">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileText className="h-8 w-8 text-primary" />
                  <div>
                    <p className="font-medium text-foreground control-text">{uploadedFile.name}</p>
                    <p className="text-sm text-muted-foreground control-text">{formatFileSize(uploadedFile.size)}</p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleRemoveFile}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </Card>

            <Button onClick={handleProcessPaper} disabled={isProcessing} className="w-full control-text">
              {isProcessing ? "Processing Paper..." : "Extract Hypotheses"}
            </Button>
          </div>
        )}
      </div>
    </Card>
  )
}
