"use client"

import * as React from "react"

export interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {
  className?: string
}

export function Label({ 
  className = "",
  children,
  ...props 
}: LabelProps) {
  return (
    <label 
      className={`text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 ${className}`} 
      {...props}
    >
      {children}
    </label>
  )
}